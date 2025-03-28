"""
Session manager for handling user sessions and access tracking.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, base_nli=None, session_timeout: int = 30):  # timeout in minutes
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout)
        self.lock = threading.Lock()
        self.base_nli = base_nli

    def create_session(self, user_id: str, token: str = None) -> Dict:
        """Create a new session for a user"""
        if not token:
            token = str(uuid.uuid4())
            
        session = {
            'user_id': user_id,
            'token': token,
            'created_at': datetime.utcnow(),
            'last_active': datetime.utcnow(),
            'ip_address': None,
            'user_agent': None,
            'conversation_id': None  # Will be populated when conversation starts
        }
        
        with self.lock:
            self.sessions[token] = session
            self._cleanup_expired_sessions()
        
        # If we have a base_nli instance, start a user session for conversation tracking
        if self.base_nli:
            self.base_nli.start_user_session(user_id)
            # Store the conversation ID for later reference
            if hasattr(self.base_nli, 'current_conversation_id'):
                session['conversation_id'] = self.base_nli.current_conversation_id
        
        return session

    def get_session(self, token: str) -> Optional[Dict]:
        """Get session information for a token"""
        session = self.sessions.get(token)
        if not session:
            return None
            
        if self._is_session_expired(session):
            self.end_session(token)
            return None
            
        session['last_active'] = datetime.utcnow()
        return session

    def update_session(self, token: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Update session metadata"""
        session = self.get_session(token)
        if not session:
            return False
            
        if ip_address:
            session['ip_address'] = ip_address
        if user_agent:
            session['user_agent'] = user_agent
            
        return True

    def end_session(self, token: str) -> bool:
        """End a user session"""
        with self.lock:
            if token in self.sessions:
                # Before removing the session, make sure any conversation data is saved
                session = self.sessions[token]
                if self.base_nli and session.get('conversation_id') and hasattr(self.base_nli, 'topic_manager'):
                    # The topic_manager will handle saving the conversation state
                    logger.info(f"Saving conversation state for session {token}")
                
                del self.sessions[token]
                return True
        return False

    def get_active_sessions(self, user_id: str = None) -> Dict[str, Dict]:
        """Get all active sessions, optionally filtered by user_id"""
        active_sessions = {}
        
        for token, session in self.sessions.items():
            if self._is_session_expired(session):
                continue
            if user_id and session['user_id'] != user_id:
                continue
            active_sessions[token] = session
            
        return active_sessions

    def resume_session(self, token: str) -> bool:
        """
        Resume a previously created session, including its conversation context
        
        Args:
            token: The session token
            
        Returns:
            Success status
        """
        session = self.get_session(token)
        if not session:
            return False
            
        # If we have a base_nli instance and the session has a conversation ID,
        # restore the conversation context
        if self.base_nli and session.get('conversation_id'):
            user_id = session['user_id']
            
            # Set the current user ID and session ID
            self.base_nli.current_user_id = user_id
            self.base_nli.session_id = token
            
            # Start the session to restore conversation context
            self.base_nli.start_user_session(user_id)
            
            return True
            
        return False

    def _is_session_expired(self, session: Dict) -> bool:
        """Check if a session has expired"""
        now = datetime.utcnow()
        last_active = session['last_active']
        return now - last_active > self.session_timeout

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        with self.lock:
            expired = [
                token for token, session in self.sessions.items()
                if self._is_session_expired(session)
            ]
            for token in expired:
                del self.sessions[token]