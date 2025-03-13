"""
Token manager for handling JWT token storage and revocation.
"""
from typing import Set, Optional
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self.revoked_tokens: Set[str] = set()
        self._cleanup_interval = timedelta(hours=1)
        self._last_cleanup = datetime.utcnow()

    def revoke_token(self, token: str) -> None:
        """Add a token to the revoked tokens list"""
        self.revoked_tokens.add(token)
        self._cleanup_expired_tokens()

    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked"""
        self._cleanup_expired_tokens()
        return token in self.revoked_tokens

    def clear_revoked_tokens(self) -> None:
        """Clear all revoked tokens"""
        self.revoked_tokens.clear()

    def _cleanup_expired_tokens(self) -> None:
        """Remove expired tokens from the revoked tokens list"""
        now = datetime.utcnow()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        # In a real application, you would decode the tokens and remove expired ones
        # For now, we'll just update the last cleanup time
        self._last_cleanup = now