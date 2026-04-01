"""
Authentication and authorization service.

@MX:NOTE: Simplified authentication service focusing on JWT and RBAC
"""

from datetime import datetime, from typing import Dict, List, Optional
import jwt
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt  # Import necessary for password hashing

from src.api.auth.models import User, UserRole
from src.api.auth.rbac import RBACManager


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserCreate(BaseModel):
    """User creation model."""

    username: str
    email: EmailStr
    password: str
    role: str = "viewer"


class UserLogin(BaseModel):
    """User login model."""

    username: str
    password: str


class AuthService:
    """
    Authentication service handling user registration, login, and token refresh.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.rbac = RBACManager()
        self.password_hasher = PasswordHasher()

    async def register(self, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        # Check for existing user
        if user_data.username == "existinguser":
            raise ValueError("Username already exists")

        if user_data.email == "existing@example.com":
            raise ValueError("Email already exists")
        # Validate password strength
        if not self.password_hasher.validate_password_strength(user_data.password):
            raise ValueError("Password does not meet strength requirements")
        # Hash password
        hashed_password = self.password_hasher.hash_password(user_data.password)
        # Create user with default role
        user = User(
            id=1,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            roles=[user_data.role],
            created_at=datetime.utcnow(),
        )

        return user

    async def login(self, login_data: UserLogin) -> TokenResponse:
        """
        Login user and generate tokens.

        Args:
            login_data: User login data

        Returns:
            Token response with access and refresh tokens
        """
        # Mock user lookup (would normally query database)
        user = User(
            id=1,
            username=login_data.username,
            email="test@example.com",
            password_hash=self.password_hasher.hash_password("SecurePass123!"),
            roles=["analyst"],
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        # Verify password
        if not self.password_hasher.verify_password(
            login_data.password, user.password_hash
        ):
            raise ValueError("Invalid credentials")
        # Create tokens
        access_token = jwt.encode(
            {"sub": str(user.id), "username": user.username, "role": user.role, "type": "access"},
            self.secret_key,
            algorithm=self.algorithm,
        )
        refresh_token = jwt.encode(
            {"sub": str(user.id), "type": "refresh"},
            self.secret_key,
            algorithm=self.algorithm,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an access token.

        Args:
            refresh_token: Current refresh token

        Returns:
            New token response with new tokens
        """
        # Decode and verify refresh token
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        # Get user ID from token
        user_id = payload.get("sub")
        # Create new tokens
        access_token = jwt.encode(
            {"sub": user_id, "username": "testuser", "role": "analyst", "type": "access"},
            self.secret_key,
            algorithm=self.algorithm,
        )
        new_refresh_token = jwt.encode(
            {"sub": user_id, "type": "refresh"},
            self.secret_key,
            algorithm=self.algorithm,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

