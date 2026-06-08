from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --------------------
# CREATE Mail
# --------------------
class MailCreate(BaseModel):
    sender: EmailStr
    recipient: EmailStr
    subject: Optional[str] = None
    body: Optional[str] = None

# --------------------
# RESPONSE MODEL
# --------------------
class MailResponse(BaseModel):
    id: int
    sender: EmailStr
    recipient: EmailStr
    subject: Optional[str]
    body: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True