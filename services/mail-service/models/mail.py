from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime, UTC

class Mail(Base):
    __tablename__ = "mails"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String)
    body = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now(UTC))