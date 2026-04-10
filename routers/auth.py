from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, UserRole
from schemas.user import UserCreate, UserLogin, UserResponse, UserChangePassword
from services.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=UserRole.user,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Registration successful", "user_id": new_user.id}


@router.post("/login")
def login(response: Response, user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and set JWT cookie."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24,  # 24 hours
        samesite="lax",
    )

    return {
        "message": "Login successful",
        "role": user.role.value,
        "user_id": user.id,
        "name": user.name,
    }


@router.post("/logout")
def logout(response: Response):
    """Logout by clearing the JWT cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password."""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    current_user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}
