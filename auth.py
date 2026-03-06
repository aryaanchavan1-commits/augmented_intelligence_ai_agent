"""
Authentication Module for Augmented Intelligence Agent
Handles user authentication, session management, and password hashing
"""

import bcrypt
import secrets
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from dotenv import load_dotenv

from database import (
    get_user_by_username,
    get_user_by_id,
    create_default_user,
    create_session,
    get_session,
    update_session_activity,
    delete_session,
    update_last_login,
    update_password
)
from logger import get_logger

# Load environment variables
load_dotenv()

# Session configuration
SESSION_TIMEOUT_MINUTES = 30
SESSION_COOKIE_NAME = "augintel_session"

# Get admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

logger = get_logger()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def init_default_user():
    """Initialize default admin user if not exists"""
    user = get_user_by_username(ADMIN_USERNAME)
    if not user:
        password_hash = hash_password(ADMIN_PASSWORD)
        user_id = create_default_user(ADMIN_USERNAME, password_hash)
        if user_id:
            logger.info(f"Created default user: {ADMIN_USERNAME}", user="system", action="init_user")
        else:
            logger.warning(f"Failed to create default user", user="system", action="init_user")
    else:
        logger.info(f"Default user already exists: {ADMIN_USERNAME}", user="system", action="init_user")


def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)


def login_user(username: str, password: str) -> Dict:
    """
    Authenticate user and create session
    Returns: dict with success status, message, and user info
    """
    # Get user from database
    user = get_user_by_username(username)
    
    if not user:
        logger.log_login(username, success=False)
        return {
            "success": False,
            "message": "Invalid username or password",
            "user": None
        }
    
    # Check if user is active
    if not user.get("is_active", True):
        logger.log_login(username, success=False)
        return {
            "success": False,
            "message": "Account is disabled",
            "user": None
        }
    
    # Verify password
    if not verify_password(password, user["password_hash"]):
        logger.log_login(username, success=False)
        return {
            "success": False,
            "message": "Invalid username or password",
            "user": None
        }
    
    # Generate session token
    session_token = generate_session_token()
    
    # Create session in database
    create_session(user["id"], session_token)
    
    # Update last login
    update_last_login(user["id"])
    
    logger.log_login(username, success=True)
    
    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "session_token": session_token
        }
    }


def logout_user(session_token: str) -> bool:
    """Logout user by deleting session"""
    if session_token:
        session = get_session(session_token)
        if session:
            username = session.get("username", "unknown")
            delete_session(session_token)
            logger.log_logout(username)
            return True
    return False


def signup_user(username: str, password: str) -> Dict:
    """
    Create a new user account
    Returns: dict with success status, message, and user info
    """
    # Validate username
    if not username or len(username) < 3:
        return {
            "success": False,
            "message": "Username must be at least 3 characters",
            "user": None
        }
    
    # Validate password
    if not password or len(password) < 6:
        return {
            "success": False,
            "message": "Password must be at least 6 characters",
            "user": None
        }
    
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        logger.warning(f"Signup failed - username already exists: {username}", user=username, action="signup_failed")
        return {
            "success": False,
            "message": "Username already exists",
            "user": None
        }
    
    # Hash password and create user
    password_hash = hash_password(password)
    user_id = create_default_user(username, password_hash)
    
    if user_id:
        logger.info(f"New user registered: {username}", user=username, action="signup_success")
        return {
            "success": True,
            "message": "Account created successfully!",
            "user": {
                "id": user_id,
                "username": username
            }
        }
    else:
        logger.error(f"Failed to create user: {username}", user=username, action="signup_failed")
        return {
            "success": False,
            "message": "Failed to create account",
            "user": None
        }


def get_current_user() -> Optional[Dict]:
    """Get current logged-in user from session"""
    # Check for session token in Streamlit session state
    if "session_token" not in st.session_state:
        return None
    
    session_token = st.session_state.get("session_token")
    if not session_token:
        return None
    
    # Get session from database
    session = get_session(session_token)
    if not session:
        # Clear only session-related state
        if "session_token" in st.session_state:
            del st.session_state["session_token"]
        return None
    
    # Update session activity (don't check timeout for now)
    update_session_activity(session_token)
    
    # Get user info
    user = get_user_by_id(session["user_id"])
    if user:
        user["session_token"] = session_token
    
    return user


def require_authentication():
    """Decorator/middleware to require authentication"""
    user = get_current_user()
    if not user:
        st.warning("Please log in to continue")
        st.switch_page("app.py")
        st.stop()
    return user


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return get_current_user() is not None


def set_session(user_info: Dict):
    """Set session in Streamlit session state"""
    st.session_state["session_token"] = user_info.get("session_token")
    st.session_state["user_id"] = user_info.get("id")
    st.session_state["username"] = user_info.get("username")


def clear_session():
    """Clear session from Streamlit session state"""
    if "session_token" in st.session_state:
        logout_user(st.session_state["session_token"])
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# Initialize default user on module import
init_default_user()
