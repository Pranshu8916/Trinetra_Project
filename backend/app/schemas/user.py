from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: str = "operator"


class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
