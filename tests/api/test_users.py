"""
User Management Endpoints Tests

Tests for user registration, profile management, and user listing.
Following TDD methodology: RED phase first.

@MX:SPEC: SPEC-PLATFORM-001 P2-T010
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        from src.api.routes.users import register_user
        from src.api.schemas.user import UserCreate
        from src.api.models.user import User

        # Mock database session
        mock_db = AsyncMock()

        # Mock user service
        mock_user_service = AsyncMock()
        mock_user = SimpleNamespace(
            id=1,
            username="newuser",
            email="newuser@example.com",
            created_at=datetime.utcnow(),
            updated_at=None
        )

        mock_user_service.create_user.return_value = mock_user

        # Request data
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!"
        )

        # Mock dependency override
        app = FastAPI()
        app.post("/api/v1/users/register", status_code=201)(register_user)

        from src.api.dependencies import get_db, get_user_service

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test registration with duplicate email fails."""
        from src.api.routes.users import register_user
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.create_user.side_effect = ValueError("Email already registered")

        app = FastAPI()
        app.post("/api/v1/users/register")(register_user)

        from src.api.dependencies import get_db, get_user_service

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request with duplicate email
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "SecurePass123!"
            }
        )

        # Verify conflict response
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_user_validation(self):
        """Test registration with invalid data fails."""
        from src.api.routes.users import register_user

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        app = FastAPI()
        app.post("/api/v1/users/register")(register_user)

        from src.api.dependencies import get_db, get_user_service

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request with invalid email
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "short"
            }
        )

        # Verify validation error
        assert response.status_code == 422


class TestUserProfileUpdate:
    """Test user profile update endpoint."""

    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test successful profile update."""
        from src.api.routes.users import update_profile
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        # Mock updated user - SimpleNamespace to avoid recursion from Mock internals
        mock_user = SimpleNamespace(
            id=1,
            username="testuser",
            email="updated@example.com",
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0)
        )

        mock_user_service.update_user.return_value = mock_user

        app = FastAPI()
        app.put("/api/v1/users/me")(update_profile)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.put(
            "/api/v1/users/me",
            json={"email": "updated@example.com"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        from src.api.routes.users import change_password
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"

        mock_user_service.change_password.return_value = True

        app = FastAPI()
        app.post("/api/v1/users/me/change-password")(change_password)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )

        # Verify response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self):
        """Test password change with wrong current password fails."""
        from src.api.routes.users import change_password

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.change_password.side_effect = ValueError("Incorrect password")

        app = FastAPI()
        app.post("/api/v1/users/me/change-password")(change_password)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request with wrong password
        response = client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456!"
            }
        )

        # Verify error response
        assert response.status_code == 400


class TestUserListing:
    """Test user listing endpoint with pagination."""

    @pytest.mark.asyncio
    async def test_list_users_success(self):
        """Test successful user listing."""
        from src.api.routes.users import list_users
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        # Mock user list - SimpleNamespace for clean serialization
        mock_users = [
            SimpleNamespace(id=1, username="user1", email="user1@example.com",
                            created_at=datetime(2025, 1, 1, 0, 0, 0), updated_at=None),
            SimpleNamespace(id=2, username="user2", email="user2@example.com",
                            created_at=datetime(2025, 1, 1, 0, 0, 0), updated_at=None),
        ]

        mock_user_service.list_users.return_value = (mock_users, 2)

        app = FastAPI()
        app.get("/api/v1/users")(list_users)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1
        mock_current_user.is_admin = True

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.get("/api/v1/users?page=1&page_size=20")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["users"]) == 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_users_forbidden(self):
        """Test user listing fails for non-admin users."""
        from src.api.routes.users import list_users

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        app = FastAPI()
        app.get("/api/v1/users")(list_users)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1
        mock_current_user.is_admin = False

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request as non-admin
        response = client.get("/api/v1/users")

        # Verify forbidden response
        assert response.status_code == 403


class TestUserDeletion:
    """Test user deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Test successful user deletion."""
        from src.api.routes.users import delete_user

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.delete_user.return_value = True

        app = FastAPI()
        app.delete("/api/v1/users/{user_id}", status_code=204)(delete_user)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1
        mock_current_user.is_admin = True

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.delete("/api/v1/users/2")

        # Verify response (204 or 200 depending on how FastAPI handles it)
        assert response.status_code in (200, 204)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        """Test deleting non-existent user fails."""
        from src.api.routes.users import delete_user

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.delete_user.return_value = False

        app = FastAPI()
        app.delete("/api/v1/users/{user_id}")(delete_user)

        from src.api.dependencies import get_db, get_user_service, get_current_user

        mock_current_user = Mock()
        mock_current_user.id = 1
        mock_current_user.is_admin = True

        async def override_get_db():
            yield mock_db

        def override_get_user_service():
            return mock_user_service

        def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request for non-existent user
        response = client.delete("/api/v1/users/999")

        # Verify not found response
        assert response.status_code == 404


class TestUserService:
    """Test user service business logic."""

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self):
        """Test that user creation hashes password."""
        from src.api.services.users import UserService
        from src.api.schemas.user import UserCreate
        from src.api.models.user import User

        mock_db = AsyncMock()

        # Mock execute to return result with no existing user
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.refresh.side_effect = lambda obj: obj

        user_service = UserService(mock_db)

        # Create user - mock hash_password to avoid bcrypt version issues
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="PlainPassword123!"
        )

        with patch('src.api.services.users.hash_password', return_value='mocked_hash'):
            user = await user_service.create_user(user_data)

        # Verify password was hashed (not stored as plain text)
        assert user.password_hash == "mocked_hash"
        assert user.password_hash != "PlainPassword123!"

    @pytest.mark.asyncio
    async def test_change_password_verifies_current(self):
        """Test password change verifies current password."""
        from src.api.services.users import UserService

        mock_db = AsyncMock()
        user_service = UserService(mock_db)

        # Mock user with existing password
        mock_user = Mock()
        mock_user.password_hash = "existing_hash"

        # Mock password verification and hashing
        with patch('src.api.services.users.verify_password') as mock_verify, \
             patch('src.api.services.users.hash_password', return_value='new_hash'):
            mock_verify.return_value = True

            # Change password
            result = await user_service.change_password(
                mock_user,
                "OldPass123!",
                "NewPass456!"
            )

            # Verify old password was checked
            mock_verify.assert_called_once_with("OldPass123!", "existing_hash")
