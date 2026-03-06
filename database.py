"""
Database Module for Augmented Intelligence Agent
Handles SQLite operations for user management and conversation history
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import os

# Database path
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "app.db"


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Messages/History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT,
            tokens_used INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Sessions table for tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            groq_api_key TEXT,
            selected_model TEXT DEFAULT 'llama-3.3-70b-versatile',
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 2048,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Migrate deprecated models (run this on startup)
    _migrate_deprecated_models()
    
    conn.commit()
    conn.close()


def _migrate_deprecated_models():
    """Migrate deprecated models to supported ones"""
    # List of deprecated models
    deprecated_models = [
        "mixtral-8x7b-32768",
        "llama-3.1-70b-versatile",
        "llama-3.1-70b-instruct",
        "mixtral-8x7b-instruct-v0.1"
    ]
    
    default_model = "llama-3.3-70b-versatile"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update any deprecated models to the default
        for model in deprecated_models:
            cursor.execute(
                "UPDATE settings SET selected_model = ? WHERE selected_model = ?",
                (default_model, model)
            )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()


def create_default_user(username: str, password_hash: str):
    """Create default admin user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        user_id = cursor.lastrowid
        
        # Create default settings for user
        cursor.execute(
            "INSERT INTO settings (user_id) VALUES (?)",
            (user_id,)
        )
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        # User already exists
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password_hash, created_at, last_login, is_active FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"],
            "last_login": row["last_login"],
            "is_active": row["is_active"]
        }
    return None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, created_at, last_login, is_active FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "created_at": row["created_at"],
            "last_login": row["last_login"],
            "is_active": row["is_active"]
        }
    return None


def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.now(), user_id)
    )
    conn.commit()
    conn.close()


def update_password(user_id: int, password_hash: str):
    """Update user's password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id)
    )
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    """Delete user and all associated data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete in correct order due to foreign keys
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


# ============= Message/History Functions =============

def save_message(
    user_id: int,
    role: str,
    content: str,
    model: str = None,
    tokens_used: int = 0,
    metadata: Dict = None
) -> int:
    """Save a message to history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    metadata_json = json.dumps(metadata) if metadata else None
    
    cursor.execute(
        """INSERT INTO messages 
           (user_id, role, content, model, tokens_used, metadata) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, role, content, model, tokens_used, metadata_json)
    )
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return message_id


def get_user_messages(
    user_id: int,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get user's message history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, role, content, model, tokens_used, timestamp, metadata 
           FROM messages 
           WHERE user_id = ? 
           ORDER BY timestamp DESC 
           LIMIT ? OFFSET ?""",
        (user_id, limit, offset)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        msg = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "model": row["model"],
            "tokens_used": row["tokens_used"],
            "timestamp": row["timestamp"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }
        messages.append(msg)
    
    return list(reversed(messages))


def get_conversation_context(user_id: int, limit: int = 10) -> List[Dict]:
    """Get recent conversation context for AI"""
    messages = get_user_messages(user_id, limit=limit)
    return messages


def search_messages(user_id: int, query: str) -> List[Dict]:
    """Search messages by content"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, role, content, model, tokens_used, timestamp, metadata 
           FROM messages 
           WHERE user_id = ? AND content LIKE ? 
           ORDER BY timestamp DESC 
           LIMIT 50""",
        (user_id, f"%{query}%")
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        msg = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "model": row["model"],
            "tokens_used": row["tokens_used"],
            "timestamp": row["timestamp"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }
        messages.append(msg)
    
    return messages


def clear_user_history(user_id: int):
    """Clear all user messages"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def export_history(user_id: int, format: str = "json") -> str:
    """Export user history to JSON or CSV"""
    messages = get_user_messages(user_id, limit=10000)
    
    if format == "json":
        return json.dumps(messages, indent=2, default=str)
    
    elif format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        if messages:
            writer = csv.DictWriter(
                output,
                fieldnames=["id", "role", "content", "model", "tokens_used", "timestamp"]
            )
            writer.writeheader()
            for msg in messages:
                writer.writerow({k: v for k, v in msg.items() if k in ["id", "role", "content", "model", "tokens_used", "timestamp"]})
        
        return output.getvalue()
    
    return str(messages)


# ============= Settings Functions =============

def get_user_settings(user_id: int) -> Dict:
    """Get user settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT groq_api_key, selected_model, temperature, max_tokens 
           FROM settings WHERE user_id = ?""",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    # Default model (always valid)
    default_model = "llama-3.3-70b-versatile"
    
    # Valid models list
    valid_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "llama-guard-4-8b",
        "llama-3.2-1b-instant",
        "llama-3.2-3b-instant"
    ]
    
    if row:
        model = row["selected_model"]
        # Validate model, use default if invalid
        if model not in valid_models:
            model = default_model
        
        return {
            "groq_api_key": row["groq_api_key"],
            "selected_model": model,
            "temperature": row["temperature"],
            "max_tokens": row["max_tokens"]
        }
    
    # Return defaults if not found
    return {
        "groq_api_key": None,
        "selected_model": default_model,
        "temperature": 0.7,
        "max_tokens": 2048
    }


def update_user_settings(
    user_id: int,
    groq_api_key: str = None,
    selected_model: str = None,
    temperature: float = None,
    max_tokens: int = None
):
    """Update user settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build update query dynamically
    updates = []
    params = []
    
    if groq_api_key is not None:
        updates.append("groq_api_key = ?")
        params.append(groq_api_key)
    
    if selected_model is not None:
        updates.append("selected_model = ?")
        params.append(selected_model)
    
    if temperature is not None:
        updates.append("temperature = ?")
        params.append(temperature)
    
    if max_tokens is not None:
        updates.append("max_tokens = ?")
        params.append(max_tokens)
    
    if updates:
        params.append(user_id)
        query = f"UPDATE settings SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()


# ============= Session Functions =============

def create_session(user_id: int, session_token: str, ip_address: str = "unknown") -> int:
    """Create a new session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (user_id, session_token, ip_address) VALUES (?, ?, ?)",
        (user_id, session_token, ip_address)
    )
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return session_id


def get_session(session_token: str) -> Optional[Dict]:
    """Get session by token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT s.id, s.user_id, s.session_token, s.created_at, s.last_activity, s.ip_address, u.username
           FROM sessions s
           JOIN users u ON s.user_id = u.id
           WHERE s.session_token = ?""",
        (session_token,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "session_token": row["session_token"],
            "created_at": row["created_at"],
            "last_activity": row["last_activity"],
            "ip_address": row["ip_address"],
            "username": row["username"]
        }
    return None


def update_session_activity(session_token: str):
    """Update session last activity timestamp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE sessions SET last_activity = ? WHERE session_token = ?",
        (datetime.now(), session_token)
    )
    conn.commit()
    conn.close()


def delete_session(session_token: str):
    """Delete a session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()


# Initialize database on module import
init_database()
