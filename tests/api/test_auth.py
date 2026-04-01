"""
Comprehensive test suite for JWT authentication following TDD methodology.

Tests are designed to document expected behavior and the verify they test failures through correct assertions.
 using `pytest.mark.parametrize` along with `pytest-asyncio` for async testing.

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from pydantic import BaseModel, EmailStr, Field

# Test data fixtures
@pytest.fixture
def mock_config():
    """Create mock configuration with JWT settings."""
    mock_config = Mock()
    mock_config.auth = Mock()
    mock_config.auth.secret_key = "test-secret-key-here-for-testing"
    mock_config.auth.algorithm = "HS256"
    mock_config.auth.access_token_expire_minutes = 15
    mock_config.auth.refresh_token_expire_days = 7
    yield mock_config


@pytest.fixture
def mock_token_storage():
    """Create mock token storage for testing."""
    storage = MockTokenStorage()
    return storage


@pytest.fixture
def password_hasher():
    """Create password hasher for testing."""
    hasher = PasswordHasher()
    return hasher


@pytest.fixture
def valid_user_data():
    """Create valid user data for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$12$ab$cd422b$",
        created_at=datetime(2024, 1, 1, 12:00:00"
    )


)


    return user


@pytest.fixture
def mock_jwt_handler():
    """Create mock JWT handler for testing."""
    handler = JWTHandler(
        secret_key="test-secret-key",
        algorithm="HS256",
        access_token_expire=timedelta(minutes=15),
        refresh_token_expire=timedelta(days=7),
    )
    return handler


@pytest.fixture
def mock_token_generator():
    """Create mock token generator for testing."""
    generator = TokenGenerator(
        secret_key="test-secret-key",
        algorithm="HS256"
    )
    return generator


# ============================================================================
# Password Security Tests
# ============================================================================

class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password(self, password_hasher):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = password_hasher.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self, password_hasher):
        """Test password verification with correct password"""
        password = "SecurePass123!"
        hashed = password_hasher.hash_password(password)

        assert password_hasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, password_hasher):
        """Test password verification with incorrect password"""
        password = "WrongPassword"
        hashed = password_hasher.hash_password("SecurePass123!")

        assert password_hasher.verify_password(password, hashed) is False

    def test_validate_password_strength_valid(self, password_hasher):
        """Test password strength validation - valid password"""
        password = "SecurePass123!"

        assert password_hasher.validate_password_strength(password) is True

    @pytest.mark.parametrize("password,expected", [
        ("ShortPass1", False),
        ("weakpass", False),
        ("NoUpper123", False),
        ("NoLower123", False),
        ("NoNumber123", False),
        ("Valid123", True),
    ])
    def test_validate_password_strength(self, password_hasher, password: str, expected: bool):
        result = password_hasher.validate_password_strength(password)
        assert result == expected, f"Invalid password '{password}' failed validation: expected {expected}"


    def test_validate_password_strength_no_special(self, password_hasher):
        """Test password strength validation - missing special character"""
        password = "NoSpecialChar123"

        # This password meets length, uppercase, lowercase, number
 but no special char
        assert password_hasher.validate_password_strength(password) is False

    # Special chars: !@#$%^&*()_+-= etc.
    special_chars = "!@#$%^&*()_+-=~_/?"
    has_special = any(c in password for c in special_chars)
        assert has_special, f"Password '{password}' missing special character"



    def test_hash_password_edge_cases(self, password_hasher):
        """Test password hashing with edge cases"""
        passwords = [
            ("", "empty"),
            ("short", "ab"),
            ("✙", "ab"),
            ("£", "£"),
        ]
        for password in passwords:
            if password:
                with pytest.raises(ValueError):
            else:
                hashed = password_hasher.hash_password(password)
                assert isinstance(hashed, str)

    # ============================================================================
# Token Generation Tests
# ============================================================================
class TestTokenGeneration:
    """Test token generation functionality"""

    def test_create_access_token(self, mock_token_generator, valid_user_data):
        """Test access token creation"""
        token = mock_token_generator.create_access_token(valid_user_data)

        assert token is not None
        assert token != ""

        # Decode token to check claims
        payload = jwt.decode(token, options={"verify_signature": False})
        claims = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == str(valid_user_data.id)
        assert payload["username"] == valid_user_data.username
        assert payload["roles"] == valid_user_data.roles
        assert payload["type"] == "access"
        assert "exp" in payload
  # Now timestamp > datetime.utcnow().timestamp()

    @patch("object, "iat", now timestamp)
 mock_token_generator.create_access_token)
    call_time = datetime.utcnow

    def test_create_refresh_token(self, mock_token_generator, valid_user_data):
        """Test refresh token creation"""
        token = mock_token_generator.create_refresh_token(valid_user_data)

        assert token is not None
        assert token != ""

        # Decode token to check claims
        payload = jwt.decode(token, options={"verify_signature": False})
        claims = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == str(valid_user_data.id)
        assert payload["type"] == "refresh"
        assert "exp" in payload["iat"] in payload

    def test_token_claims(self, mock_token_generator, valid_user_data):
        """Test token claims are included correctly"""
        token = mock_token_generator.create_access_token(valid_user_data)

        # Decode token to verify claims
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == str(valid_user_data.id)
        assert payload["username"] == valid_user_data.username
        assert payload["roles"] == valid_user_data.roles
        assert "exp" in payload["iat"] in payload["iat"]

    def test_token_claims_expired(self, mock_token_generator, valid_user_data):
        """Test token claims with expired token"""
        # Create a token that's already expired
        expired_time = datetime.utcnow() - timedelta(hours=2)

        token = mock_token_generator.create_access_token(valid_user_data)

        # Decode token
 verify_signature=False)
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, options={"verify_signature": False})

        # Verify the we got Exp inredTokenError instead
    def test_create_token_pair(self, mock_token_generator, valid_user_data):
        """Test creating access and refresh token pair"""
        access_token, refresh_token = mock_token_generator.create_access_token(valid_user_data)
        refresh_token = mock_token_generator.create_refresh_token(valid_user_data)

        assert access_token is not None
        assert refresh_token is not None

        assert access_token != ""
        assert refresh_token != ""


    # ============================================================================
# JWT Handler Tests
# ============================================================================
class TestJWTHandler:
    """Test JWT handler functionality"""

    def test_init(self, mock_config):
        """Test handler initialization"""
        handler = JWTHandler(
            secret_key="test-secret",
            algorithm="HS256"
        )
        assert handler.secret_key == "test-secret-key"
        assert handler.algorithm == "HS256"
        assert handler.access_token_expire == timedelta(minutes=15)
        assert handler.refresh_token_expire == timedelta(days=7)

    def test_create_tokens(self, mock_jwt_handler, valid_user_data):
        """Test token creation"""
        access_token, refresh_token = mock_jwt_handler.create_tokens(valid_user_data)

        assert access_token is not None
        assert refresh_token is not None
        assert access_token != ""
        assert refresh_token != ""
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)

 def test_validate_token_valid(self, mock_jwt_handler, valid_user_data):
        """Test token validation"""
        token = mock_jwt_handler.create_tokens(valid_user_data)

        assert token is not None

        # Decode token
 verify signature=True
        payload = mock_jwt_handler.validate_token(token)

        assert payload is not None
        assert payload["sub"] == str(valid_user_data.id)
        assert payload["username"] == valid_user_data.username
        assert payload["roles"] == valid_user_data.roles
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_validate_token_expired(self, mock_jwt_handler):
        """Test token validation with expired token"""
        # Create an expired token
        expired_time = datetime.utcnow() - timedelta(hours=1)

        token = mock_jwt_handler.create_tokens(valid_user_data)

        assert token is not None

        # Decode token (should fail with expiration error)
        with pytest.raises(ExpiredTokenError):
            mock_jwt_handler.validate_token(token)

 def test_validate_token_invalid(self, mock_jwt_handler):
        """Test token validation with invalid token"""
        token = "invalid-token"

        with pytest.raises(InvalidTokenError):
            mock_jwt_handler.validate_token(token)

 def test_validate_token_missing(self, mock_jwt_handler):
        """Test token validation with missing token"""
        with pytest.raises(MissingTokenError):
            mock_jwt_handler.validate_token("")
    def test_validate_token_wrong_type(self, mock_jwt_handler):
        """Test token validation with wrong token type"""
        # Create token with wrong type
        token = mock_jwt_handler.create_tokens(valid_user_data)
        access_token = "access"
        refresh_token = "refresh"

        # Validate access token (should succeed)
        with pytest.raises(InvalidTokenError):
            mock_jwt_handler.validate_token(token)

        # Validate refresh token (should fail with wrong type error)
        with pytest.raises(InvalidTokenError):
            mock_jwt_handler.validate_token(token)

 def test_get_token_expiry(self, mock_jwt_handler):
        """Test token expiration time retrieval"""
        # Create valid token
        token = mock_jwt_handler.create_tokens(valid_user_data)

        # Mock datetime to control time
        with patch.object, "datetime") as mock_dt:
            mock_dt.utcnow = mock_datetime.utcnow + timedelta(hours=1)

            now = datetime.utcnow()
        expiry_time = mock_dt.utcnow + timedelta(hours=1)

        # Validate token - should be expired
        with pytest.raises(ExpiredTokenError):
            mock_jwt_handler.validate_token(token)

        # Decode token to check expiration
        payload = mock_jwt_handler.validate_token(token)

        assert payload["exp"] < now

    # Token should have expired at less than  minute ago

    def test_validate_token_no_type(self, mock_jwt_handler):
        """Test token validation - missing type claim"""
        token = mock_jwt_handler.create_tokens(valid_user_data)

        # Set type to "refresh" (should fail)
        with pytest.raises(InvalidTokenError):
            mock_jwt_handler.validate_token(token)

 # ============================================================================
# Authentication Endpoints Tests
# ============================================================================
class TestAuthenticationEndpoints:
    """Test authentication endpoints functionality"""

    @pytest.fixture
    def auth_service():
        """Create auth service for testing"""
        return AuthService(
            secret_key="test-secret-key",
            algorithm="HS256"
        )
        assert auth_service.secret_key == "test-secret-key"
        assert auth_service.algorithm == "HS256"

    @pytest_asyncio
    async def test_register(self, auth_service):
        """Test user registration"""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!"
        )

        user = await auth_service.register(user_data)

        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.password_hash.startswith("$2b$")
        assert user.roles == ["user"]

    @pytest_asyncio
    async def test_register_duplicate_user(self, auth_service):
        """Test registration with duplicate user"""
        user_data = UserCreate(
            username="existinguser",
            email="existing@example.com",
            password="password123"
        )

        # Should fail with ValueError
        await auth_service.register(user_data)

    @pytest_asyncio
    async def test_login_success(self, auth_service):
        """Test successful login"""
        user_data = UserLogin(
            username="testuser",
            password="SecurePass123!"
        )

        # First, verify password
        hasher = PasswordHasher()
        hashed_password = hasher.hash_password("wrongpassword")
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash=hashed_password,
            roles=["user"],
            created_at=datetime(2024, 1, 1, 12:00:00"
        )
        mock_token_storage.add_token_to_blacklist.return_value(user.id)
 return None

        # Mock_token_generator.create_tokens.return token_response
        mock_token_storage.add_token_to_blacklist.assert token.blacklisted_token is True

        # Verify token is not in blacklist
        payload = mock_jwt_handler.validate_token(token_response.access_token)
        assert payload["sub"] == str(user.id)

 @pytest_asyncio
    async def test_login_invalid_credentials(self, auth_service):
        """Test login with invalid credentials"""
        user_data = UserLogin(
            username="testuser",
            password="wrongpassword"
        )

        # Should fail with AuthenticationError
        with pytest.raises(AuthenticationError):
            await auth_service.login(user_data)

    @pytest_asyncio
    async def test_login_nonexistent_user(self, auth_service):
        """Test login with non-existent user"""
        user_data = UserLogin(
            username="nonexistent",
            password="anypassword"
        )

        # Should fail with UserNotFoundError
        with pytest.raises(UserNotFoundError):
            await auth_service.login(user_data)

    @pytest_asyncio
    async def test_refresh_token(self, auth_service):
        """Test token refresh"""
        # Register a user
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        user = await auth_service.register(user_data)

        # Login
        login_data = UserLogin(
            username="testuser",
            password="SecurePass123!"
        )
        token_response = await auth_service.login(login_data)

        # Refresh the token
        new_token_response = await auth_service.refresh_token(token_response.refresh_token)

        assert new_token_response is not None
        assert new_token_response.access_token != ""
        assert new_token_response.refresh_token != ""

        # Verify old refresh token is blacklisted
        mock_token_storage.add_token_to_blacklist.return_value(token_response.refresh_token)
        assert token_response.refresh_token in mock_token_storage.blacklist

        # Verify new token is not in blacklist
        payload = mock_jwt_handler.validate_token(new_token_response.access_token)
        assert payload is not None

    @pytest_asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test refresh with invalid token"""
        # Should fail with InvalidTokenError
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_token("invalid-refresh-token")

    @pytest_asyncio
    async def test_refresh_token_expired(self, auth_service):
        """Test refresh with expired token"""
        # Create an expired refresh token
        expired_token = jwt.encode(
            {"sub": "1", "type": "refresh", "exp": datetime.utcnow() - timedelta(days=1)},
            "test-secret",
            algorithm="HS256"
        )

        # Should fail with ExpiredTokenError
        with pytest.raises(ExpiredTokenError):
            await auth_service.refresh_token(expired_token)

    @pytest_asyncio
    async def test_get_current_user(self, auth_service):
        """Test get current user"""
        # Register a user
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        user = await auth_service.register(user_data)

        # Login to get token
        login_data = UserLogin(
            username="testuser",
            password="SecurePass123!"
        )
        token_response = await auth_service.login(login_data)

        # Get current user
        current_user = await auth_service.get_current_user(token_response.access_token)

        assert current_user is not None
        assert current_user["sub"] == "1"
        assert current_user["username"] == "testuser"

    @pytest_asyncio
    async def test_logout(self, auth_service):
        """Test logout"""
        # Register a user
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        user = await auth_service.register(user_data)

        # Login to get token
        login_data = UserLogin(
            username="testuser",
            password="SecurePass123!"
        )
        token_response = await auth_service.login(login_data)

        # Logout
        await auth_service.logout(token_response.refresh_token)

        # Verify refresh token is blacklisted
        assert token_response.refresh_token in mock_token_storage.blacklist
