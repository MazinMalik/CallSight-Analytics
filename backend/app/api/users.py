from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserCreate
from app.api.auth import get_current_user
from app.core import security

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@router.post("/", response_model=UserOut)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Create new telecaller (Admin only)
    """
    user = db.query(User).filter(User.login_id == user_in.login_id).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this login ID already exists in the system.",
        )
    
    user = User(
        login_id=user_in.login_id,
        name=user_in.name,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role if user_in.role else "telecaller"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/", response_model=List[UserOut])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Retrieve users (Admin only)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users
