from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    login_id: str
    name: str
    password: str
    role: Optional[str] = "telecaller"

class UserOut(BaseModel):
    id: str
    login_id: str
    name: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
