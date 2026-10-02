from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field




class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse




class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str | None
    status: str
    chunk_count: int
    upload_date: datetime




class ResearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    route: str | None
    answer: str | None
    created_at: datetime
