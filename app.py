"""
Augmented Intelligence Agent - Main Application
Streamlit web interface for the AI-powered augmented intelligence system
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv

# Import modules
import auth
import database
import groq_agent
import workflow as wf
from logger import get_logger
from groq_agent import GROQ_MODELS

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger()

# Page configuration
st.set_page_config(
    page_title="AugInted Agent by aryan chavan",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-bg: #0D1117;
        --secondary-bg: #161B22;
        --accent-blue: #58A6FF;
        --accent-green: #7EE787;
        --text-primary: #E6EDF3;
        --text-secondary: #8B949E;
        --border-color: #30363D;
        --error: #F85149;
        --warning: #D29922;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--primary-bg);
        color: var(--text-primary);
    }
    
    /* Card styling */
    .card {
        background-color: var(--secondary-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        max-width: 85%;
    }
    
    .chat-message.user {
        background-color: var(--accent-blue);
        color: white;
        margin-left: auto;
    }
    
    .chat-message.assistant {
        background-color: var(--secondary-bg);
        border: 1px solid var(--border-color);
    }
    
    .chat-message .timestamp {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    
    /* Workflow step styling */
    .workflow-step {
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        border-left: 3px solid var(--border-color);
    }
    
    .workflow-step.pending {
        border-left-color: var(--text-secondary);
        background-color: rgba(139, 148, 158, 0.1);
    }
    
    .workflow-step.running {
        border-left-color: var(--accent-blue);
        background-color: rgba(88, 166, 255, 0.1);
    }
    
    .workflow-step.completed {
        border-left-color: var(--accent-green);
        background-color: rgba(126, 231, 135, 0.1);
    }
    
    .workflow-step.failed {
        border-left-color: var(--error);
        background-color: rgba(248, 81, 73, 0.1);
    }
    
    /* Sidebar styling */
    .sidebar-section {
        padding: 12px;
        background-color: var(--secondary-bg);
        border-radius: 6px;
        margin-bottom: 12px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: var(--secondary-bg);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 6px;
    }
    
    .stButton > button:hover {
        background-color: #4393E6;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-indicator.online {
        background-color: var(--accent-green);
    }
    
    .status-indicator.offline {
        background-color: var(--error);
    }
</style>
""", unsafe_allow_html=True)


# ============= Session State Initialization =============

def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "username" not in st.session_state:
        st.session_state.username = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "workflow_context" not in st.session_state:
        st.session_state.workflow_context = None
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "llama-3.3-70b-versatile"
    
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7


# ============= Authentication Functions =============

def show_login_page():
    """Display login page"""
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="color: #E6EDF3; margin-bottom: 8px;">🧠 AugIntel Agent</h1>
        <p style="color: #8B949E; margin-bottom: 32px;">Augmented Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Tab selection for Login/Signup
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
            
            with tab1:
                st.markdown("### Login")
                
                login_username = st.text_input("Username", placeholder="Enter username", key="login_user")
                login_password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
                
                login_btn = st.button("Login", use_container_width=True, key="login_btn")
                
                if login_btn:
                    if login_username and login_password:
                        result = auth.login_user(login_username, login_password)
                        
                        if result["success"]:
                            auth.set_session(result["user"])
                            st.session_state.authenticated = True
                            st.session_state.user_id = result["user"]["id"]
                            st.session_state.username = result["user"]["username"]
                            st.rerun()
                        else:
                            st.error(result["message"])
                    else:
                        st.warning("Please enter username and password")
            
            with tab2:
                st.markdown("### Create Account")
                
                signup_username = st.text_input("Username", placeholder="Choose a username (min 3 chars)", key="signup_user")
                signup_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 chars)", key="signup_pass")
                signup_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm")
                
                signup_btn = st.button("Sign Up", use_container_width=True, key="signup_btn")
                
                if signup_btn:
                    if signup_username and signup_password and signup_confirm:
                        if signup_password != signup_confirm:
                            st.error("Passwords do not match!")
                        else:
                            result = auth.signup_user(signup_username, signup_password)
                            
                            if result["success"]:
                                st.success(result["message"])
                                st.info("Please login with your new credentials")
                            else:
                                st.error(result["message"])
                    else:
                        st.warning("Please fill in all fields")
            
            st.markdown('</div>', unsafe_allow_html=True)


# ============= Main Application Functions =============

def show_sidebar():
    """Display sidebar with navigation and user info"""
    with st.sidebar:
        # User info
        st.markdown("### 👤 User")
        st.markdown(f"**{st.session_state.username}**")
        st.markdown(f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_")
        
        st.divider()
        
        # Navigation
        st.markdown("### 📋 Menu")
        
        menu_options = ["💬 Chat", "📜 History", "⚙️ Settings"]
        selected_menu = st.radio("Navigation", menu_options, label_visibility="collapsed")
        
        st.divider()
        
        # Settings section
        st.markdown("### ⚙️ Quick Settings")
        
        # Model selection - with error handling
        model_options = list(GROQ_MODELS.keys())
        current_model = st.session_state.get("selected_model", "llama-3.3-70b-versatile")
        
        # Find index safely - ensure model is in list
        if current_model not in model_options:
            current_model = "llama-3.3-70b-versatile"
        
        try:
            model_index = model_options.index(current_model)
        except:
            model_index = 0
        
        selected_model = st.selectbox(
            "AI Model",
            model_options,
            index=model_index,
            format_func=lambda x: GROQ_MODELS[x]["name"],
            key="sidebar_model"
        )
        
        # Temperature - with error handling
        current_temp = st.session_state.get("temperature", 0.7)
        try:
            temp_value = float(current_temp) if 0.0 <= float(current_temp) <= 1.0 else 0.7
        except:
            temp_value = 0.7
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=temp_value,
            step=0.1,
            key="sidebar_temp"
        )
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            auth.clear_session()
            st.session_state.authenticated = False
            st.rerun()
        
        # Version info
        st.markdown("""
        <div style="text-align: center; color: #8B949E; font-size: 11px; margin-top: 20px;">
            AugIntel Agent v1.0.0<br>
            Powered by Groq API
        </div>
        """, unsafe_allow_html=True)
    
    return selected_menu


def show_chat_page():
    """Display main chat interface"""
    # Page header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## 💬 Augmented Intelligence Chat")
    with col2:
        # Status indicator
        agent = st.session_state.get("agent")
        if agent and agent.client:
            st.markdown('<span class="status-indicator online"></span> AI Online', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator offline"></span> AI Offline', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        for msg in st.session_state.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div>{content}</div>
                    <div class="timestamp">{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div>{content}</div>
                    <div class="timestamp">{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Workflow panel (collapsible)
    with st.expander("🔄 Workflow Progress", expanded=False):
        if st.session_state.workflow_context:
            context = st.session_state.workflow_context
            for step in context.workflow_steps:
                status_class = step.status.value
                duration = f"{step.duration():.2f}s" if step.duration() > 0 else ""
                
                st.markdown(f"""
                <div class="workflow-step {status_class}">
                    <strong>{step.name}</strong>
                    <span style="color: #8B949E; font-size: 12px;"> - {step.description}</span>
                    <br>
                    <span style="font-size: 11px; color: #8B949E;">
                        Status: {status_class.capitalize()} {duration}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                if step.error:
                    st.error(f"Error: {step.error}")
        else:
            st.info("No workflow running. Start a conversation to see the workflow.")
    
    st.markdown("---")
    
    # Input area
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Ask anything...",
            placeholder="Type your message here...",
            key="user_input",
            label_visibility="collapsed"
        )
    with col2:
        send_btn = st.button("Send", use_container_width=True)
    
    # Handle send
    if send_btn and user_input:
        # Add user message
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Save to database
        if st.session_state.get("user_id"):
            database.save_message(
                user_id=st.session_state.user_id,
                role="user",
                content=user_input
            )
        
        # Get AI response
        process_message(user_input)
        
        # Clear input and rerun
        st.rerun()


def process_message(user_input: str):
    """Process user message through the augmented intelligence workflow"""
    agent = st.session_state.get("agent")
    
    if not agent or not agent.client:
        # No agent configured
        error_msg = {
            "role": "assistant",
            "content": "⚠️ AI agent not configured. Please set up your Groq API key in Settings.",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(error_msg)
        
        if st.session_state.get("user_id"):
            database.save_message(
                user_id=st.session_state.user_id,
                role="assistant",
                content=error_msg["content"]
            )
        return
    
    # Get conversation history
    history = []
    if st.session_state.get("user_id"):
        history = database.get_conversation_context(st.session_state.user_id, limit=10)
    
    # Create workflow context
    context = wf.create_workflow_context(
        user_input=user_input,
        user_id=st.session_state.user_id,
        username=st.session_state.username,
        conversation_history=history
    )
    
    # Create and execute workflow
    workflow = wf.AugmentedIntelligenceWorkflow()
    
    # Run workflow synchronously
    try:
        # For simplicity, we'll run the workflow steps directly
        # Note: In production, you'd use async/await properly
        
        # Step 1: Input Processing
        context = asyncio.run(_run_step(context, "Input Processing", "Parse and validate input", wf.step_input_processing))
        
        # Step 2: Context Gathering
        context = asyncio.run(_run_step(context, "Context Gathering", "Retrieve relevant context", wf.step_context_gathering))
        
        # Step 3: AI Analysis
        context = asyncio.run(_run_step(context, "AI Analysis", "Generate AI response", lambda ctx: wf.step_ai_analysis(ctx, agent)))
        
        # Step 4: Workflow Execution  
        context = asyncio.run(_run_step(context, "Workflow Execution", "Execute requested actions", wf.step_workflow_execution))
        
        # Step 5: Result Formatting
        context = asyncio.run(_run_step(context, "Result Formatting", "Format response", wf.step_result_formatting))
        
        # Extract final response from result formatting step
        formatting_step = context.get_step("Result Formatting")
        if formatting_step and formatting_step.result:
            context.final_response = formatting_step.result.get("formatted_response", "")
        
        # Store workflow context
        st.session_state.workflow_context = context
        
        # Get final response
        response_text = context.final_response if context.final_response else "I apologize, but I couldn't generate a response."
        
    except Exception as e:
        logger.log_error(st.session_state.username, e, "Workflow execution")
        response_text = f"Error processing your request: {str(e)}"
    
    # Add assistant message
    assistant_message = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    st.session_state.messages.append(assistant_message)
    
    # Save to database
    if st.session_state.get("user_id"):
        database.save_message(
            user_id=st.session_state.user_id,
            role="assistant",
            content=response_text,
            model=st.session_state.get("selected_model", "llama-3.3-70b-versatile")
        )


async def _run_step(context, name, description, step_func):
    """Helper to run a workflow step"""
    step = wf.WorkflowStep(name=name, description=description, status=wf.WorkflowStatus.RUNNING)
    step.start_time = datetime.now()
    context.add_step(step)
    
    try:
        result = await step_func(context)
        step.result = result
        step.status = wf.WorkflowStatus.COMPLETED
    except Exception as e:
        step.error = str(e)
        step.status = wf.WorkflowStatus.FAILED
    finally:
        step.end_time = datetime.now()
    
    return context


def show_history_page():
    """Display conversation history"""
    st.markdown("## 📜 Conversation History")
    st.markdown("---")
    
    if not st.session_state.get("user_id"):
        st.error("Please log in to view history")
        return
    
    # Get messages from database
    messages = database.get_user_messages(st.session_state.user_id, limit=100)
    
    if not messages:
        st.info("No conversation history yet. Start chatting to build your history!")
        return
    
    # Search functionality
    search_query = st.text_input("🔍 Search history", placeholder="Search messages...")
    
    if search_query:
        messages = database.search_messages(st.session_state.user_id, search_query)
        st.markdown(f"Found {len(messages)} matching messages")
    
    # Display messages
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        icon = "👤" if role == "user" else "🤖"
        
        with st.expander(f"{icon} {role.capitalize()} - {timestamp}"):
            st.markdown(content)
    
    # Export options
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Export JSON", use_container_width=True):
            json_data = database.export_history(st.session_state.user_id, "json")
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name="conversation_history.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📥 Export CSV", use_container_width=True):
            csv_data = database.export_history(st.session_state.user_id, "csv")
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="conversation_history.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🗑️ Clear History", type="primary", use_container_width=True):
            database.clear_user_history(st.session_state.user_id)
            st.success("History cleared!")
            st.rerun()


def show_settings_page():
    """Display settings page"""
    st.markdown("## ⚙️ Settings")
    st.markdown("---")
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Please log in to access settings")
        return
    
    # Get current settings
    settings = database.get_user_settings(user_id)
    
    # API Key section
    st.markdown("### 🔑 Groq API Configuration")
    
    api_key = st.text_input(
        "Groq API Key",
        value=settings.get("groq_api_key", ""),
        type="password",
        help="Get your API key from https://console.groq.com"
    )
    
    if api_key:
        # Validate API key
        if st.button("✓ Validate API Key"):
            if groq_agent.validate_api_key(api_key):
                st.success("API key is valid!")
            else:
                st.error("Invalid API key")
    
    # Model selection
    st.markdown("### 🤖 Model Settings")
    
    model_options = list(GROQ_MODELS.keys())
    current_setting_model = settings.get("selected_model", "llama-3.3-70b-versatile")
    
    # Ensure model is valid
    if current_setting_model not in model_options:
        current_setting_model = "llama-3.3-70b-versatile"
    
    try:
        model_index = model_options.index(current_setting_model)
    except:
        model_index = 0
    
    selected_model = st.selectbox(
        "AI Model",
        model_options,
        index=model_index,
        format_func=lambda x: f"{GROQ_MODELS[x]['name']} ({GROQ_MODELS[x]['context_window']//1000}K context)"
    )
    
    # Model description
    if selected_model:
        st.info(GROQ_MODELS[selected_model]["description"])
    
    # Generation settings
    st.markdown("### ⚡ Generation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=settings.get("temperature", 0.7),
            step=0.1,
            help="Controls randomness. Lower = more focused, Higher = more creative"
        )
    
    with col2:
        max_tokens = st.slider(
            "Max Tokens",
            min_value=256,
            max_value=8192,
            value=settings.get("max_tokens", 2048),
            step=256,
            help="Maximum number of tokens in the response"
        )
    
    # Save button
    st.markdown("---")
    
    if st.button("💾 Save Settings", use_container_width=True):
        # Update settings in database
        database.update_user_settings(
            user_id=user_id,
            groq_api_key=api_key if api_key else None,
            selected_model=selected_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Update session state
        st.session_state.selected_model = selected_model
        st.session_state.temperature = temperature
        
        # Reinitialize agent
        if api_key:
            st.session_state.agent = groq_agent.GroqAgent(
                api_key=api_key,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        st.success("Settings saved!")
        st.rerun()
    
    # Current settings display
    st.markdown("---")
    st.markdown("### 📊 Current Settings")
    
    st.markdown(f"""
    | Setting | Value |
    |---------|-------|
    | Model | {GROQ_MODELS.get(selected_model, {}).get('name', selected_model)} |
    | Temperature | {temperature} |
    | Max Tokens | {max_tokens} |
    | API Key | {'✓ Configured' if api_key else '✗ Not set'} |
    """)
    
    # Profile section
    st.markdown("---")
    st.markdown("### 👤 Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Username:** {st.session_state.username}")
        st.markdown(f"**User ID:** {user_id}")
    
    with col2:
        # Change password
        st.markdown("#### Change Password")
        current_pass = st.text_input("Current Password", type="password", key="current_pass")
        new_pass = st.text_input("New Password", type="password", key="new_pass")
        confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass")
        
        if st.button("Update Password"):
            if current_pass and new_pass and confirm_pass:
                if new_pass != confirm_pass:
                    st.error("New passwords do not match!")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    # Verify current password
                    user = database.get_user_by_id(user_id)
                    if user and auth.verify_password(current_pass, user["password_hash"]):
                        # Update password
                        new_hash = auth.hash_password(new_pass)
                        database.update_password(user_id, new_hash)
                        logger.info(f"Password updated for user: {st.session_state.username}", user=st.session_state.username, action="password_changed")
                        st.success("Password updated successfully!")
                    else:
                        st.error("Current password is incorrect")
            else:
                st.warning("Please fill in all password fields")
    
    # Account management
    st.markdown("---")
    st.markdown("### 🗑️ Account Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export all data
        if st.button("📥 Export My Data", use_container_width=True):
            json_data = database.export_history(user_id, "json")
            st.download_button(
                label="Download My Data (JSON)",
                data=json_data,
                file_name=f"{st.session_state.username}_data.json",
                mime="application/json"
            )
    
    with col2:
        # Delete account
        st.warning("⚠️ Danger Zone")
        delete_confirm = st.text_input("Type 'DELETE' to confirm", placeholder="DELETE", key="delete_confirm")
        
        if st.button("🗑️ Delete My Account", type="primary", use_container_width=True):
            if delete_confirm == "DELETE":
                # Delete user account
                success = database.delete_user(user_id)
                if success:
                    logger.warning(f"User account deleted: {st.session_state.username}", user=st.session_state.username, action="account_deleted")
                    auth.clear_session()
                    st.session_state.authenticated = False
                    st.success("Account deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete account")
            else:
                st.warning("Please type 'DELETE' to confirm")


# ============= Main Application =============

def main():
    """Main application entry point"""
    # Initialize session state first
    init_session_state()
    
    # Get user from session
    user = auth.get_current_user()
    
    if user:
        # User is logged in, show main app
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        
        # Initialize agent
        settings = database.get_user_settings(user["id"])
        
        # Validate model - ensure it's in the supported list
        valid_models = list(groq_agent.GROQ_MODELS.keys())
        selected_model = settings.get("selected_model", "llama-3.3-70b-versatile")
        if selected_model not in valid_models:
            selected_model = "llama-3.3-70b-versatile"
            # Update the invalid model in database
            database.update_user_settings(user_id=user["id"], selected_model=selected_model)
        
        if settings.get("groq_api_key") and not st.session_state.get("agent"):
            st.session_state.agent = groq_agent.GroqAgent(
                api_key=settings["groq_api_key"],
                model=selected_model,
                temperature=settings.get("temperature", 0.7),
                max_tokens=settings.get("max_tokens", 2048)
            )
            st.session_state.selected_model = selected_model
            st.session_state.temperature = settings.get("temperature", 0.7)
        
        # Show main app
        selected_menu = show_sidebar()
        
        if selected_menu == "💬 Chat":
            show_chat_page()
        elif selected_menu == "📜 History":
            show_history_page()
        elif selected_menu == "⚙️ Settings":
            show_settings_page()
    else:
        # Show login page
        show_login_page()


if __name__ == "__main__":
    main()
