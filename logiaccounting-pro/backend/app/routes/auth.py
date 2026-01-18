"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.store import db
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_roles
)
from app.schemas.schemas import (
    LoginRequest, LoginResponse, RegisterRequest,
    ProfileUpdate, PasswordChange, UserStatusUpdate
)
from app.services.two_factor import two_factor_service

router = APIRouter()


@router.post("/login")
async def login(request: LoginRequest):
    """User login endpoint"""
    user = db.users.find_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active"
        )

    if two_factor_service.is_2fa_enabled(user["id"]):
        return {
            "requires_2fa": True,
            "email": user["email"],
            "message": "Please enter your 2FA code"
        }

    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    user_data = {k: v for k, v in user.items() if k != "password"}

    return {"success": True, "token": token, "user": user_data}


@router.post("/verify-2fa")
async def verify_2fa_login(email: str, code: str):
    """Verify 2FA code during login"""
    user = db.users.find_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not two_factor_service.verify_login(user["id"], code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    user_data = {k: v for k, v in user.items() if k != "password"}

    return {"success": True, "token": token, "user": user_data}


@router.post("/logout")
async def logout():
    """User logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return {k: v for k, v in current_user.items() if k != "password"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """User registration endpoint"""
    if db.users.find_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(request.password)
    user = db.users.create({
        "email": request.email,
        "password": hashed_password,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "role": request.role,
        "company_name": request.company_name,
        "phone": request.phone
    })
    
    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    return {"success": True, "token": token, "user": user}


@router.put("/profile")
async def update_profile(
    request: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    updated = db.users.update(current_user["id"], update_data)
    return {k: v for k, v in updated.items() if k != "password"}


@router.put("/password")
async def change_password(
    request: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    if not verify_password(request.current_password, current_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    hashed = get_password_hash(request.new_password)
    db.users.update_password(current_user["id"], hashed)
    return {"success": True, "message": "Password changed successfully"}


@router.get("/users")
async def get_users(current_user: dict = Depends(require_roles("admin"))):
    """Get all users (admin only)"""
    return db.users.find_all_safe()


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    request: UserStatusUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update user status (admin only)"""
    updated = db.users.update(user_id, {"status": request.status})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {k: v for k, v in updated.items() if k != "password"}
