from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserCreate
from app.services.user_service import UserService
from app.api.v1.deps import (
    get_current_user, 
    get_current_active_user, 
    require_admin_role, 
    require_platform_admin,
    require_tenant_admin,
    get_tenant_from_user
)
from app.models.user import UserRole

router = APIRouter()


@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=None)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    user_service = UserService(db)
    
    # Users cannot change their own role
    if user_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    updated_user = await user_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user account (soft delete)"""
    user_service = UserService(db)
    success = await user_service.delete_user(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User account deleted successfully"}


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get users list (admin only)"""
    user_service = UserService(db)
    
    # Platform admin can see all users
    if current_user.role == UserRole.PLATFORM_ADMIN:
        users = await user_service.get_all_users(skip=skip, limit=limit)
    else:
        # Tenant admin can only see users in their tenant
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant access"
            )
        users = await user_service.get_users_by_tenant(tenant_id, skip=skip, limit=limit)
    
    return users


@router.post("/", response_model=None)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = await user_service.get_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Tenant admin can only create users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant access"
            )
        user_data.tenant_id = tenant_id
        
        # Tenant admin cannot create platform admin users
        if user_data.role == UserRole.PLATFORM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create platform admin users"
            )
    
    user = await user_service.create_user(user_data)
    return user


@router.get("/{user_id}", response_model=None)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin can only access users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return user


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Update user by ID (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin can only update users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Tenant admin cannot change users to platform admin
        if user_update.role == UserRole.PLATFORM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change user role to platform admin"
            )
    
    updated_user = await user_service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Delete user by ID (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Tenant admin can only delete users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Activate user account (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Tenant admin can only activate users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.activate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account (admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot deactivate yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Tenant admin can only deactivate users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant_id = await get_tenant_from_user(current_user)
        if not tenant_id or target_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    """Change user role (platform admin only)"""
    user_service = UserService(db)
    
    # Get target user
    target_user = await user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await user_service.change_user_role(user_id, new_role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User role changed to {new_role.value}"}
