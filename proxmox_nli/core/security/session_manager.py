"""
Session manager for handling user sessions and access tracking.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading

class SessionManager:
    def __init__(self, session_timeout: int = 30):  # timeout in minutes
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout)
        self.lock = threading.Lock()

    def create_session(self, user_id: str, token: str) -> Dict:
        """Create a new session for a user"""
        session = {
            'user_id': user_id,
            'token': token,
            'created_at': datetime.utcnow(),
            'last_active': datetime.utcnow(),
            'ip_address': None,
            'user_agent': None
        }
        
        with self.lock:
            self.sessions[token] = session
            self._cleanup_expired_sessions()
        
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