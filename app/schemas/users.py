from pydantic import BaseModel

# Pydantic schema for validating product creation
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str