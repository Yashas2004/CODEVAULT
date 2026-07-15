from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class SnippetCreate(BaseModel):
    title: str
    language: str
    code: str
    tags: Optional[str] = ""

# backend/app/schemas.py
class SnippetOut(SnippetCreate):
    id: int
    created_at: datetime
    is_public: bool = False
    share_slug: Optional[str] = None
    class Config:
        from_attributes = True

class PaginatedSnippets(BaseModel):
    items: list[SnippetOut]
    next_cursor: Optional[int] = None
    has_more: bool


class ShareResponse(BaseModel):
    share_slug: str
    is_public: bool

class PublicSnippetOut(BaseModel):
    title: str
    language: str
    code: str
    tags: Optional[str] = ""
    created_at: datetime
    class Config:
        from_attributes = True