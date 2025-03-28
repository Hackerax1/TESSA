"""
Tests for security components including authentication, permissions, and sessions.
"""
import pytest
from datetime import datetime, timedelta
import jwt
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from proxmox_nli.core.security.auth_manager import AuthManager
from proxmox_nli.core.security.permission_handler import PermissionHandler
from proxmox_nli.core.security.token_manager import TokenManager
from proxmox_nli.core.security.session_manager import SessionManager

@pytest.fixture
def auth_manager():
    return AuthManager()

@pytest.fixture
def permission_handler():
    return PermissionHandler()

@pytest.fixture
def token_manager():
    return TokenManager()

@pytest.fixture
def session_manager():
    return SessionManager(session_timeout=1)  # 1 minute timeout for testing

class TestAuthManager:
    def test_create_token(self, auth_manager):
        token = auth_manager.create_token('test_user', ['admin'])
        assert token is not None
        
        payload = auth_manager.verify_token(token)
        assert payload['user_id'] == 'test_user'
        assert 'admin' in payload['roles']

    def test_verify_token(self, auth_manager):
        token = auth_manager.create_token('test_user')
        assert auth_manager.verify_token(token) is not None
        
        # Test invalid token
        assert auth_manager.verify_token('invalid_token') is None

    def test_check_permission(self, auth_manager):
        admin_token = auth_manager.create_token('admin_user', ['admin'])
        user_token = auth_manager.create_token('regular_user', ['user'])
        
        assert auth_manager.check_permission(admin_token, ['admin'])
        assert auth_manager.check_permission(user_token, ['user'])
        assert auth_manager.check_permission(admin_token, ['user'])  # Admin has all permissions
        assert not auth_manager.check_permission(user_token, ['admin'])

class TestPermissionHandler:
    def test_has_permission(self, permission_handler):
        assert permission_handler.has_permission(['admin'], 'vm.create')  # Admin has all permissions
        assert permission_handler.has_permission(['user'], 'vm.view')
        assert not permission_handler.has_permission(['user'], 'unknown.permission')

    def test_add_remove_permission(self, permission_handler):
        permission_handler.add_role_permission('custom_role', 'custom.permission')
        assert permission_handler.has_permission(['custom_role'], 'custom.permission')
        
        permission_handler.remove_role_permission('custom_role', 'custom.permission')
        assert not permission_handler.has_permission(['custom_role'], 'custom.permission')

class TestTokenManager:
    def test_token_revocation(self, token_manager):
        token = 'test_token'
        assert not token_manager.is_token_revoked(token)
        
        token_manager.revoke_token(token)
        assert token_manager.is_token_revoked(token)
        
        token_manager.clear_revoked_tokens()
        assert not token_manager.is_token_revoked(token)

class TestSessionManager:
    def test_session_lifecycle(self, session_manager):
        session = session_manager.create_session('test_user', 'test_token')
        assert session['user_id'] == 'test_user'
        assert session['token'] == 'test_token'
        
        # Test session retrieval
        retrieved = session_manager.get_session('test_token')
        assert retrieved is not None
        assert retrieved['user_id'] == 'test_user'
        
        # Test session end
        assert session_manager.end_session('test_token')
        assert session_manager.get_session('test_token') is None

    def test_session_expiry(self, session_manager):
        session = session_manager.create_session('test_user', 'test_token')
        
        # Force session expiration by manipulating last_active
        session['last_active'] = datetime.utcnow() - timedelta(minutes=2)
        
        # Session should be expired and removed
        assert session_manager.get_session('test_token') is None

    def test_active_sessions(self, session_manager):
        session_manager.create_session('user1', 'token1')
        session_manager.create_session('user2', 'token2')
        
        sessions = session_manager.get_active_sessions()
        assert len(sessions) == 2
        
        user_sessions = session_manager.get_active_sessions('user1')
        assert len(user_sessions) == 1