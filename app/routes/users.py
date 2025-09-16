from fastapi import APIRouter, HTTPException

from app.models.user import User
from app.schemas.users import UserCreate
from app.database import SessionLocal
from app.core.security import hash_password, verify_password, create_JWT

router = APIRouter()

# get all users
@router.get("/")
def get_users():
    with SessionLocal() as session:
        users = session.query(User).all()
        return {"users": users}

# create new user
@router.post("/register")
def register(user_data: UserCreate):
    with SessionLocal() as session:
        matching_user = session.query(User).filter(User.username == user_data.username).first()
        if matching_user:
            return {"message": "Username already registered"}
        else:
            user_dict = user_data.model_dump()
            user_dict['password_hash'] = hash_password(user_data.password)
            del user_dict['password']
            new_user = User(**user_dict)
            session.add(new_user)
            session.commit()
            return {"message": "User created!"}
    
# gets a JWT token
@router.post("/login")
def login(user_data: UserCreate):
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == user_data.username).first()
        if user:
            if verify_password(user_data.password, user.password_hash):
                return {"access_token": create_JWT({"sub": user.username, "user_id": user.id})}
            else:
                return {"message": "Incorrect password!"}
        else:
            return {"message": "Username not found!"}
    
# Delete a user by id
@router.delete("/{user_id}")
def delete_user(user_id: int):
    with SessionLocal() as session:
        user_to_delete = session.query(User).filter(User.id == user_id).first()
        if user_to_delete:
            session.delete(user_to_delete)
            session.commit()
            return {"message": "User deleted!"}
        else:
            raise HTTPException(status_code=404, detail="User not found!")