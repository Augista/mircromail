from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal
from models.mail import Mail, MailBox
from schemas.mail import MailCreate, MailResponse
from lib.event import publish_mail_sent

from config import settings

app = FastAPI(
    title="MicroMail Mail Service",
    description="Mail service responsible for delivering and managing mails",
    version="1.0.0"
)
origins = [  "http://localhost",
    "http://localhost:3000",]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------
# DB DEPENDENCY
# --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------
# HEALTH
# --------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------
# CREATE MAIL
# --------------------
@app.post("/mails", response_model=MailResponse, status_code=201)
def create_mail(payload: MailCreate, db: Session = Depends(get_db)):
    mail = Mail(
        sender=payload.sender,
        recipient=payload.recipient,
        subject=payload.subject,
        body=payload.body,
        status="sent"
    )

    db.add(mail)
    db.commit()
    db.refresh(mail)

    publish_mail_sent(mail)

    return mail

# --------------------
# GET ALL MAILS
# --------------------
@app.get("/mails", response_model=List[MailResponse])
def get_mails(
    email: str, 
    box: MailBox, # inbox | sent | all
    search: str = Query(None),
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db)):
    query = db.query(Mail)

    if box == "inbox":
        query = query.filter(Mail.recipient == email)

    elif box == "sent":
        query = query.filter(Mail.sender == email)

    else:
        query = query.filter(
            (Mail.sender == email) | (Mail.recipient == email)
        )

    if search:
        query = query.filter(
            or_(
                Mail.subject.ilike(f"%{search}%"),
                Mail.body.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Mail.id.desc())

    return query.offset(skip).limit(limit).all()


# --------------------
# GET MAIL
# --------------------
@app.get("/mails/{mail_id}", response_model=MailResponse)
def get_mail(mail_id: int, db: Session = Depends(get_db)):
    mail = db.query(Mail).filter(Mail.id == mail_id).first()

    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    return mail


# --------------------
# DELETE MAIL
# --------------------
@app.delete("/mails/{mail_id}")
def delete_mail(
    mail_id: int, 
    email: str,
    db: Session = Depends(get_db)):
    mail = db.query(Mail).filter(
        Mail.id == mail_id,
        Mail.sender == email
    ).first()

    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    db.delete(mail)
    db.commit()

    return {"message": "Mail deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.MAIL_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )