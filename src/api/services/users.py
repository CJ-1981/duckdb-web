"""
User Service

Business logic for user management operations.
Includes registration, profile updates, password management.

@MX:SPEC: SPEC-PLATFORM-001 P2-T010
"""

from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from passlib.context import CryptContext

from src.api.models.user import User
from src.api.schemas.user import UserCreate, UserUpdate


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service for user business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with hashed password.

        Args:
            user_data: User creation data

        Returns:
            Created user object

        @MX:ANCHOR: User creation entry point (fan_in >= 3: registration, admin creation, tests)
        """
        # Check if email already exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Check if username already exists
        existing = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Username already taken")

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found

        @MX:ANCHOR: Email lookup entry point (fan_in >= 3: auth, registration, password reset)
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user object or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        # Update fields
        if user_data.email is not None:
            # Check if email already exists for another user
            existing = await self.db.execute(
                select(User).where(
                    and_(
                        User.email == user_data.email,
                        User.id != user_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Email already in use")

            user.email = user_data.email

        if user_data.username is not None:
            # Check if username already exists for another user
            existing = await self.db.execute(
                select(User).where(
                    and_(
                        User.username == user_data.username,
                        User.id != user_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Username already taken")

            user.username = user_data.username

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user: User object
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed, False otherwise

        @MX:ANCHOR: Password change entry point (fan_in >= 3: profile update, reset, forced change)
        """
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Incorrect password")

        # Hash new password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        return True

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        List users with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Optional search term for username/email

        Returns:
            Tuple of (users list, total count)
        """
        query = select(User)

        # Apply search filter
        if search:
            query = query.where(
                (User.username.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and associated data.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found

        @MX:NOTE: Cascades to workflows, jobs, and other user data
        """
        user = await self.get_user(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()

        return True


# Password utility functions

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    @MX:ANCHOR: Password hashing (fan_in >= 3: creation, change, reset)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise

    @MX:ANCHOR: Password verification (fan_in >= 3: login, change, verification)
    """
    return pwd_context.verify(plain_password, hashed_password)


__all__ = [
    'UserService',
    'hash_password',
    'verify_password'
]
