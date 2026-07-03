from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = 'doctor'

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: str = 'doctor'

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str = 'doctor'

class TokenData(BaseModel):
    username: Optional[str] = None
