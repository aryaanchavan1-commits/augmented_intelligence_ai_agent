"""
Augmented Intelligence Workflow Module
Defines the workflow system for processing user requests through multiple stages
"""

import json
import re
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import streamlit as st

from logger import get_logger

logger = get_logger()


class WorkflowStatus(Enum):
    """Workflow step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in the workflow"""
    name: str
    description: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def duration(self) -> float:
        """Calculate step duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class WorkflowContext:
    """Context passed through workflow steps"""
    user_input: str
    user_id: int
    username: str
    conversation_history: List[Dict] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    final_response: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def add_step(self, step: WorkflowStep):
        """Add a workflow step"""
        self.workflow_steps.append(step)
    
    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name"""
        for step in self.workflow_steps:
            if step.name == name:
                return step
        return None


class Workflow:
    """Base workflow class for augmented intelligence"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps: List[Callable] = []
    
    def add_step(self, func: Callable, name: str, description: str):
        """Add a step to the workflow"""
        self.steps.append({
            "func": func,
            "name": name,
            "description": description
        })
    
    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Execute the workflow"""
        logger.log_workflow(
            username=context.username,
            workflow=self.name,
            step="start",
            status="started"
        )
        
        for step_info in self.steps:
            step = WorkflowStep(
                name=step_info["name"],
                description=step_info["description"],
                status=WorkflowStatus.RUNNING
            )
            step.start_time = datetime.now()
            context.add_step(step)
            
            logger.log_workflow(
                username=context.username,
                workflow=self.name,
                step=step.name,
                status="running"
            )
            
            try:
                # Execute step
                result = await step_info["func"](context)
                step.result = result
                step.status = WorkflowStatus.COMPLETED
                
                logger.log_workflow(
                    username=context.username,
                    workflow=self.name,
                    step=step.name,
                    status="completed"
                )
                
            except Exception as e:
                step.error = str(e)
                step.status = WorkflowStatus.FAILED
                
                logger.log_workflow(
                    username=context.username,
                    workflow=self.name,
                    step=step.name,
                    status="failed"
                )
                
                # Continue to next step or stop based on error handling
                if not self.continue_on_error(context, step):
                    break
            
            finally:
                step.end_time = datetime.now()
        
        logger.log_workflow(
            username=context.username,
            workflow=self.name,
            step="end",
            status="completed"
        )
        
        return context
    
    def continue_on_error(self, context: WorkflowContext, step: WorkflowStep) -> bool:
        """Determine if workflow should continue after error"""
        return False


# ============= Predefined Workflow Steps =============

async def step_input_processing(context: WorkflowContext) -> Dict:
    """
    Step 1: Input Processing
    Parse and validate user input, extract intent and entities
    """
    user_input = context.user_input or ""
    
    # Basic parsing
    result = {
        "original_input": user_input,
        "cleaned_input": user_input.strip() if user_input else "",
        "word_count": len(user_input.split()) if user_input else 0,
        "char_count": len(user_input) if user_input else 0,
        "detected_intent": detect_intent(user_input) if user_input else "general",
        "entities": extract_entities(user_input) if user_input else []
    }
    
    return result


async def step_context_gathering(context: WorkflowContext) -> Dict:
    """
    Step 2: Context Gathering
    Retrieve relevant context from conversation history
    """
    # Get recent conversation history
    history = context.conversation_history[-5:] if context.conversation_history else []
    
    result = {
        "history_length": len(history),
        "relevant_context": [],
        "context_summary": ""
    }
    
    # Extract relevant context based on current input
    current_input = (context.user_input or "").lower()
    
    for msg in history:
        if msg.get("role") == "user":
            content = (msg.get("content", "") or "").lower()
            # Simple relevance check
            current_words = set(current_input.split()) if current_input else set()
            content_words = set(content.split()) if content else set()
            common_words = current_words & content_words
            if len(common_words) >= 2:
                result["relevant_context"].append({
                    "content": (msg.get("content", "") or "")[:100],
                    "relevance_score": len(common_words)
                })
    
    # Summarize context
    if result["relevant_context"]:
        result["context_summary"] = f"Found {len(result['relevant_context'])} relevant previous messages"
    else:
        result["context_summary"] = "No relevant context found in history"
    
    return result


async def step_ai_analysis(context: WorkflowContext, agent) -> Dict:
    """
    Step 3: AI Analysis
    Use Groq to analyze and generate response with enhanced prompts
    """
    from groq_agent import GroqAgent
    
    # Get the agent instance from context
    if not agent:
        return {
            "success": False,
            "error": "AI agent not available. Please configure your Groq API key in Settings.",
            "response": None
        }
    
    # Build conversation messages
    messages = []
    for msg in context.conversation_history[-10:]:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    
    # Get processing result
    processing_step = context.get_step("Input Processing")
    if processing_step and processing_step.result:
        cleaned_input = processing_step.result.get("cleaned_input", context.user_input)
    else:
        cleaned_input = context.user_input
    
    # Get detected intent for context-aware response
    intent = "general"
    if processing_step and processing_step.result:
        intent = processing_step.result.get("detected_intent", "general")
    
    # Build enhanced system prompt based on intent
    system_prompt = get_enhanced_system_prompt(intent, context)
    
    # Generate response
    response = agent.generate(
        user_input=cleaned_input,
        context=messages,
        system_prompt=system_prompt
    )
    
    return response


def get_enhanced_system_prompt(intent: str, context: WorkflowContext) -> str:
    """Get enhanced system prompt based on detected intent"""
    base_prompt = """You are an Advanced Augmented Intelligence Agent designed to help users with various real-world tasks.
Your role is to assist, analyze, and provide actionable insights while augmenting human capabilities.

Guidelines:
- Be clear, concise, and helpful
- Provide step-by-step explanations when appropriate
- Suggest actions or workflows that can automate tasks
- When dealing with code, provide complete, working examples
- When analyzing data, provide insights and interpretations
- Always prioritize user safety and ethical considerations"""
    
    intent_prompts = {
        "information": """You are a knowledgeable research assistant. When users ask for information:
- Provide comprehensive, accurate answers
- Include relevant context and background
- Cite sources when possible
- Offer to dive deeper into any aspect""",
        
        "action": """You are a task execution assistant. When users want to accomplish tasks:
- Break down complex tasks into manageable steps
- Provide clear action plans
- Anticipate potential issues and solutions
- Follow up with progress checks""",
        
        "analysis": """You are an analytical consultant. When users need analysis:
- Examine data or problems systematically
- Identify patterns and relationships
- Provide insights and recommendations
- Support conclusions with evidence""",
        
        "question": """You are a helpful Q&A assistant. When users ask questions:
- Answer directly and thoroughly
- Provide examples when helpful
- Clarify any ambiguities
- Offer additional related information""",
        
        "conversation": """You are a friendly AI assistant. For casual conversations:
- Be warm and engaging
- Maintain context from previous messages
- Remember user preferences"""
    }
    
    intent_prompt = intent_prompts.get(intent, intent_prompts.get("general", ""))
    
    # Add conversation context if available
    if context.conversation_history:
        context_info = f"\n\nThis is conversation #{len(context.conversation_history) + 1}. Previous context may be relevant."
    else:
        context_info = "\n\nThis is the start of a new conversation."
    
    return f"{base_prompt}\n\n{intent_prompt}{context_info}"


async def step_workflow_execution(context: WorkflowContext) -> Dict:
    """
    Step 4: Workflow Execution
    Execute requested actions based on AI response
    """
    # This step can be extended to perform various actions
    # like calling APIs, running code, etc.
    
    result = {
        "actions_executed": [],
        "success": True
    }
    
    # Example: Check if user wants to execute code
    ai_response_step = context.get_step("AI Analysis")
    if ai_response_step and ai_response_step.result:
        response_text = ai_response_step.result.get("response", "")
        
        # Handle None or empty response
        if response_text:
            # Detect if response contains action items
            if "execute" in response_text.lower() or "run" in response_text.lower():
                result["actions_executed"].append({
                    "type": "code_execution",
                    "status": "pending_user_confirmation"
                })
    
    return result


async def step_result_formatting(context: WorkflowContext) -> Dict:
    """
    Step 5: Result Formatting
    Present results with sources and formatting
    """
    ai_response_step = context.get_step("AI Analysis")
    
    result = {
        "formatted_response": "",
        "sources": [],
        "suggestions": []
    }
    
    if ai_response_step and ai_response_step.result:
        response = ai_response_step.result.get("response", "")
        
        # Handle None or empty response
        if response:
            # Format response with markdown
            result["formatted_response"] = format_response(response)
            
            # Add suggestions based on workflow
            workflow_steps = context.workflow_steps
            if workflow_steps:
                result["suggestions"] = [
                    "Ask for clarification if needed",
                    "Request more details on any topic",
                    "Try a different workflow or task"
                ]
    
    return result


# ============= Helper Functions =============

def detect_intent(text: str) -> str:
    """Simple intent detection"""
    if not text:
        return "general"
    
    text_lower = text.lower()
    
    # Define intent patterns
    intents = {
        "information": ["what", "how", "why", "explain", "tell me"],
        "action": ["do", "make", "create", "build", "run"],
        "analysis": ["analyze", "compare", "evaluate", "assess"],
        "question": ["?", "can you", "could you", "would you"],
        "conversation": ["hello", "hi", "hey", "thanks", "thank you"]
    }
    
    for intent, keywords in intents.items():
        for keyword in keywords:
            if keyword in text_lower:
                return intent
    
    return "general"


def extract_entities(text: str) -> List[Dict]:
    """Simple entity extraction"""
    if not text:
        return []
    
    entities = []
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        entities.append({"type": "url", "value": url})
    
    # Extract code blocks
    code_pattern = r'`([^`]+)`'
    code_blocks = re.findall(code_pattern, text)
    for code in code_blocks:
        entities.append({"type": "code", "value": code})
    
    # Extract numbers
    number_pattern = r'\b\d+\b'
    numbers = re.findall(number_pattern, text)
    for num in numbers:
        entities.append({"type": "number", "value": num})
    
    return entities


def format_response(text: str) -> str:
    """Format response with markdown"""
    # Handle None or empty text
    if not text:
        return ""
    
    # Ensure proper line breaks
    formatted = text.strip()
    
    # Add code block formatting if needed
    if "```" not in formatted and any(kw in formatted.lower() for kw in ["code", "function", "def ", "class "]):
        pass  # Code block detection can be enhanced here
    
    return formatted


# ============= Main Augmented Intelligence Workflow =============

class AugmentedIntelligenceWorkflow:
    """Main augmented intelligence workflow"""
    
    def __init__(self):
        self.name = "Augmented Intelligence"
        self.description = "Process user requests through AI-powered analysis"
    
    async def execute(
        self,
        context: WorkflowContext,
        agent
    ) -> WorkflowContext:
        """Execute the full augmented intelligence workflow"""
        
        # Step 1: Input Processing
        context = await self._execute_step(
            context,
            "Input Processing",
            "Parse and validate user input",
            step_input_processing
        )
        
        # Step 2: Context Gathering
        context = await self._execute_step(
            context,
            "Context Gathering",
            "Retrieve relevant context from history",
            step_context_gathering
        )
        
        # Step 3: AI Analysis
        context = await self._execute_step(
            context,
            "AI Analysis",
            "Analyze and generate response using Groq",
            lambda ctx: step_ai_analysis(ctx, agent)
        )
        
        # Step 4: Workflow Execution
        context = await self._execute_step(
            context,
            "Workflow Execution",
            "Execute requested actions",
            step_workflow_execution
        )
        
        # Step 5: Result Formatting
        context = await self._execute_step(
            context,
            "Result Formatting",
            "Format and present results",
            step_result_formatting
        )
        
        # Set final response
        formatting_step = context.get_step("Result Formatting")
        if formatting_step and formatting_step.result:
            context.final_response = formatting_step.result.get("formatted_response", "")
        
        return context
    
    async def _execute_step(
        self,
        context: WorkflowContext,
        name: str,
        description: str,
        step_func: callable
    ) -> WorkflowContext:
        """Execute a single workflow step"""
        step = WorkflowStep(
            name=name,
            description=description,
            status=WorkflowStatus.RUNNING
        )
        step.start_time = datetime.now()
        context.add_step(step)
        
        logger.log_workflow(
            username=context.username,
            workflow=self.name,
            step=name,
            status="running"
        )
        
        try:
            result = await step_func(context)
            step.result = result
            step.status = WorkflowStatus.COMPLETED
            
            logger.log_workflow(
                username=context.username,
                workflow=self.name,
                step=name,
                status="completed"
            )
            
        except Exception as e:
            step.error = str(e)
            step.status = WorkflowStatus.FAILED
            
            logger.log_workflow(
                username=context.username,
                workflow=self.name,
                step=name,
                status="failed"
            )
        
        finally:
            step.end_time = datetime.now()
        
        return context


def create_workflow_context(
    user_input: str,
    user_id: int,
    username: str,
    conversation_history: List[Dict] = None
) -> WorkflowContext:
    """Create a new workflow context"""
    return WorkflowContext(
        user_input=user_input,
        user_id=user_id,
        username=username,
        conversation_history=conversation_history or []
    )
