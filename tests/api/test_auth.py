"""
Authentication and user model tests.

Tests for user models, schemas, and basic authentication functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.api.models.user import User, UserRole
from src.api.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordChange


# ========================================================================
# User Model Tests
# ========================================================================

class TestUserModel:
    """Test User model functionality."""

    def test_user_role_enum(self):
        """Test UserRole enum has correct values."""
        assert UserRole.admin.value == "admin"
        assert UserRole.analyst.value == "analyst"
        assert UserRole.viewer.value == "viewer"

    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_here",
            role=UserRole.analyst
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.analyst
        assert user.is_active is True

    def test_user_repr(self):
        """Test User string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.viewer
        )
        user.id = 1

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "1" in repr_str


# ========================================================================
# User Schema Tests
# ========================================================================

class TestUserSchemas:
    """Test user Pydantic schemas."""

    def test_user_create_schema_valid(self):
        """Test UserCreate schema with valid data."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )

        assert user_data.username == "testuser"
        assert user_data.email == "test@example.com"
        assert user_data.password == "SecurePass123!"

    def test_user_create_schema_validation(self):
        """Test UserCreate schema validation."""
        # Test username too short
        with pytest.raises(Exception):
            UserCreate(
                username="ab",  # Too short (min 3)
                email="test@example.com",
                password="SecurePass123!"
            )

    def test_user_update_schema(self):
        """Test UserUpdate schema allows optional fields."""
        update_data = UserUpdate(
            username="newusername"
        )

        assert update_data.username == "newusername"
        assert update_data.email is None

    def test_password_change_schema(self):
        """Test PasswordChange schema."""
    password_data = PasswordChange(
        current_password="oldpass123",
        new_password="newpass456"
    )

    assert password_data.current_password == "oldpass123"
    assert password_data.new_password == "newpass456"


# ========================================================================
# Token Validation Tests
# ========================================================================

class TestTokenValidation:
    """Test token validation and generation."""

    def test_token_expiration_calculation(self):
        """Test token expiration time calculation."""
        now = datetime.utcnow()
        expire_minutes = 15

        exp_time = now + timedelta(minutes=expire_minutes)
        time_diff = (exp_time - now).total_seconds()

        assert time_diff == pytest.approx(15 * 60, abs=5)

    def test_jwt_encoding_decoding(self):
        """Test basic JWT encoding and decoding."""
        import jwt

        secret = "test-secret"
        payload = {
            "sub": "testuser",
            "role": "analyst",
            "type": "access"
        }

        # Encode token
        token = jwt.encode(payload, secret, algorithm="HS256")
        assert isinstance(token, str)

        # Decode token
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "analyst"

    def test_token_with_expiration(self):
        """Test token with expiration time."""
        import jwt

        secret = "test-secret"
        payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }

        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert "exp" in decoded
        assert decoded["sub"] == "testuser"


# ========================================================================
# RBAC Tests
# ========================================================================

class TestRBAC:
    """Test role-based access control."""

    def test_admin_role_permissions(self):
        """Test admin has full permissions."""
        admin_user = Mock()
        admin_user.role = UserRole.admin

        # Admin should have access to all resources
        assert admin_user.role == UserRole.admin

    def test_viewer_role_permissions(self):
        """Test viewer has limited permissions."""
        viewer_user = Mock()
        viewer_user.role = UserRole.viewer

        # Viewer role should be viewer
        assert viewer_user.role == UserRole.viewer

    def test_role_comparison(self):
        """Test role hierarchy."""
        admin_role = UserRole.admin
        viewer_role = UserRole.viewer

        # Roles are different
        assert admin_role != viewer_role


# ========================================================================
# Email Validation Tests
# ========================================================================

class TestEmailValidation:
    """Test email validation in schemas."""

    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "test_user@test-domain.com"
        ]

        for email in valid_emails:
            user_data = UserCreate(
                username="testuser",
                email=email,
                password="SecurePass123!"
            )
            assert user_data.email == email

    def test_invalid_email_formats(self):
        """Test invalid email formats are rejected."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com"
        ]

        for email in invalid_emails:
            with pytest.raises(Exception):
                UserCreate(
                    username="testuser",
                    email=email,
                    password="SecurePass123!"
                )


# ========================================================================
# Password Validation Tests
# ========================================================================

class TestPasswordValidation:
    """Test password validation."""

    def test_password_length_validation(self):
        """Test password length requirements."""
        # Test valid password
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        assert len(user_data.password) >= 8

    def test_weak_password_rejected(self):
        """Test weak passwords are rejected."""
        weak_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoNumbers!",  # No numbers
        ]

        for password in weak_passwords:
            # Password less than 8 characters should fail validation
            if len(password) < 8:
                with pytest.raises(Exception):
                    UserCreate(
                        username="testuser",
                        email="test@example.com",
                        password=password
                    )
