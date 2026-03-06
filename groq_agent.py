"""
Groq API Integration Module for Augmented Intelligence Agent
Handles communication with Groq's LLM API for AI-powered responses
"""

import os
from typing import List, Dict, Optional, Generator, Any
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

from logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger()

# Available Groq models (all currently supported models)
GROQ_MODELS = {
    "llama-3.3-70b-versatile": {
        "name": "Llama 3.3 70B Versatile",
        "context_window": 128000,
        "description": "Latest Llama model, great for general tasks"
    },
    "llama-3.1-8b-instant": {
        "name": "Llama 3.1 8B Instant",
        "context_window": 128000,
        "description": "Fast, efficient for simple tasks"
    },
    "gemma2-9b-it": {
        "name": "Gemma 2 9B",
        "context_window": 8192,
        "description": "Google's efficient instruction model"
    },
    "llama-guard-4-8b": {
        "name": "Llama Guard 4 8B",
        "context_window": 128000,
        "description": "Safety-focused model for content filtering"
    },
    "llama-3.2-1b-instant": {
        "name": "Llama 3.2 1B Instant",
        "context_window": 128000,
        "description": "Ultra-fast model for simple tasks"
    },
    "llama-3.2-3b-instant": {
        "name": "Llama 3.2 3B Instant",
        "context_window": 128000,
        "description": "Fast model with good performance"
    }
}


class GroqAgent:
    """Groq API agent for augmented intelligence"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.api_key = api_key
        # Ensure model is valid
        if model not in GROQ_MODELS:
            model = "llama-3.3-70b-versatile"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        
        if api_key:
            self._init_client()
    
    def _init_client(self):
        """Initialize Groq client"""
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"Groq client initialized with model: {self.model}", user="system", action="init_groq")
        except Exception as e:
            logger.log_error("system", e, "Failed to initialize Groq client")
            raise
    
    def update_settings(
        self,
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """Update agent settings"""
        if api_key is not None:
            self.api_key = api_key
            self._init_client()
        
        if model is not None:
            # Ensure model is valid
            if model in GROQ_MODELS:
                self.model = model
            else:
                logger.warning(f"Invalid model: {model}, keeping {self.model}", user="system", action="update_settings")
        
        if temperature is not None:
            self.temperature = temperature
        
        if max_tokens is not None:
            self.max_tokens = max_tokens
        
        logger.info(
            f"Updated settings - Model: {self.model}, Temp: {self.temperature}, MaxTokens: {self.max_tokens}",
            user="system",
            action="update_settings"
        )
    
    def format_conversation(self, messages: List[Dict]) -> List[Dict]:
        """Format conversation history for API"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append({"role": role, "content": content})
        return formatted
    
    def generate(
        self,
        user_input: str,
        context: List[Dict] = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Generate AI response (non-streaming)
        Returns: dict with response, tokens_used, and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq client not initialized. Please configure your API key.",
                "response": None,
                "tokens_used": 0
            }
        
        # Build messages
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # Default system prompt for augmented intelligence
            messages.append({
                "role": "system",
                "content": """You are an Augmented Intelligence Agent designed to help users with various tasks.
Your role is to assist, analyze, and provide actionable insights while augmenting human capabilities.
Be clear, concise, and helpful. When appropriate, suggest actions or workflows that can automate tasks."""
            })
        
        # Add conversation context
        if context:
            messages.extend(self.format_conversation(context))
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.log_api_call(
                username=st.session_state.get("username", "unknown"),
                model=self.model,
                tokens_used=tokens_used
            )
            
            return {
                "success": True,
                "response": assistant_message,
                "tokens_used": tokens_used,
                "model": self.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.log_error(
                username=st.session_state.get("username", "unknown"),
                error=e,
                context="Groq API call"
            )
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "tokens_used": 0
            }
    
    def generate_streaming(
        self,
        user_input: str,
        context: List[Dict] = None,
        system_prompt: str = None
    ) -> Generator[str, None, None]:
        """
        Generate AI response with streaming
        Yields: response chunks as they're generated
        """
        if not self.client:
            yield "Error: Groq client not initialized. Please configure your API key."
            return
        
        # Build messages
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system",
                "content": """You are an Augmented Intelligence Agent designed to help users with various tasks.
Your role is to assist, analyze, and provide actionable insights while augmenting human capabilities.
Be clear, concise, and helpful. When appropriate, suggest actions or workflows that can automate tasks."""
            })
        
        # Add conversation context
        if context:
            messages.extend(self.format_conversation(context))
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        total_tokens = 0
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                
                if chunk.usage:
                    total_tokens = chunk.usage.total_tokens
            
            # Log after completion
            logger.log_api_call(
                username=st.session_state.get("username", "unknown"),
                model=self.model,
                tokens_used=total_tokens
            )
            
        except Exception as e:
            logger.log_error(
                username=st.session_state.get("username", "unknown"),
                error=e,
                context="Groq API streaming call"
            )
            yield f"Error: {str(e)}"


def get_available_models() -> Dict:
    """Get list of available Groq models"""
    return GROQ_MODELS


def validate_api_key(api_key: str) -> bool:
    """Validate Groq API key by making a test request"""
    try:
        client = Groq(api_key=api_key)
        # Make a minimal request to validate
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return True
    except Exception:
        return False
