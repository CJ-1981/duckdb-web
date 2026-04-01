"""
User Management Routes

API endpoints for user registration, profile management,
and user administration.

@MX:SPEC: SPEC-PLATFORM-001 P2-T010
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User
from src.api.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordChange, UserListResponse
from src.api.services.users import UserService
from src.api.dependencies import get_user_service, get_current_user
from src.api.models.base import get_async_session

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        user_service: User service

    Returns:
        Created user

    Raises:
        409: If email or username already exists
    """
    async with get_async_session() as db:
        service = UserService(db)
        try:
            user = await service.create_user(user_data)
            return user
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.

    Args:
        current_user: Authenticated user

    Returns:
        Current user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile.

    Args:
        user_data: Update data
        current_user: Authenticated user
        user_service: User service

    Returns:
        Updated user profile

    Raises:
        409: If email or username already in use
    """
    try:
        updated_user = await user_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change current user password.

    Args:
        password_data: Current and new password
        current_user: Authenticated user
        user_service: User service

    Returns:
        Success message

    Raises:
        400: If current password is incorrect
    """
    try:
        await user_service.change_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    List users (admin only).

    Args:
        page: Page number
        page_size: Items per page
        search: Optional search term
        current_user: Authenticated user (must be admin)
        user_service: User service

    Returns:
        Paginated user list

    Raises:
        403: If user is not admin
    """
    # Check admin permission
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    users, total = await user_service.list_users(page, page_size, search)

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete a user (admin only).

    Args:
        user_id: ID of user to delete
        current_user: Authenticated user (must be admin)
        user_service: User service

    Raises:
        403: If user is not admin
        404: If user not found
    """
    # Check admin permission
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = await user_service.delete_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


__all__ = ['router']
