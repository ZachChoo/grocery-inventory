from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

from app.models.user import User
from app.schemas.users import UserCreate
from app.database import SessionLocal
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.config import settings


router = APIRouter()

# get all users with pagination
@router.get("/")
def get_users(page: int = 1, size: int = settings.DEFAULT_PAGE_SIZE):
    if size > settings.MAX_PAGE_SIZE:
            size = settings.MAX_PAGE_SIZE
    with SessionLocal() as session:
        skip = (page - 1) * size
        users = session.query(User).offset(skip).limit(size).all()
        return {
            "users": users,
            "page": page,
            "size": size
            }

# create new user
@router.post("/register")
def register(user_data: UserCreate):
    with SessionLocal() as session:
        matching_user = session.query(User).filter(User.username == user_data.username).first()
        if matching_user:
            raise HTTPException(status_code=400, detail="User already registered")
        else:
            user_dict = user_data.model_dump()
            user_dict['password_hash'] = hash_password(user_data.password)
            del user_dict['password']
            new_user = User(**user_dict)
            session.add(new_user)
            session.commit()
            return {"message": "User created!"}

# verify password for login attempt
def authenticate_user(username: str, password: str):
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not verify_password(password, user.password_hash):
            return False
        return user

# gets a JWT token
@router.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }
    
def require_role(required_role: str):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Delete a user by id. User must be a manager
@router.delete("/{user_id}")
def delete_user(user_id: int,  _: Annotated[User, Depends(require_role("manager"))]):
    with SessionLocal() as session:
        user_to_delete = session.query(User).filter(User.id == user_id).first()
        if user_to_delete:
            session.delete(user_to_delete)
            session.commit()
            return {"message": "User deleted!"}
        else:
            raise HTTPException(status_code=404, detail="User not found!")