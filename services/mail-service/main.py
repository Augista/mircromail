from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models.mail import Mail
from schemas.mail import MailCreate, MailUpdate, MailResponse


app = FastAPI(
    title="MicroMail Mail Service",
    description="Mail service responsible for delivering and managing mails",
    version="1.0.0"
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
        status="pending"
    )

    db.add(mail)
    db.commit()
    db.refresh(mail)

    return mail

# --------------------
# GET ALL MAILS
# --------------------
@app.get("/mails", response_model=List[MailResponse])
def get_mails(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Mail).offset(skip).limit(limit).all()


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
# UPDATE MAIL
# --------------------
@app.patch("/mails/{mail_id}", response_model=MailResponse)
def update_mail(mail_id: int, payload: MailUpdate, db: Session = Depends(get_db)):
    mail = db.query(Mail).filter(Mail.id == mail_id).first()

    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    if payload.subject is not None:
        mail.subject = payload.subject

    if payload.body is not None:
        mail.body = payload.body

    if payload.status is not None:
        mail.status = payload.status

    db.commit()
    db.refresh(mail)

    return mail


# --------------------
# DELETE MAIL
# --------------------
@app.delete("/mails/{mail_id}")
def delete_mail(mail_id: int, db: Session = Depends(get_db)):
    mail = db.query(Mail).filter(Mail.id == mail_id).first()

    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    db.delete(mail)
    db.commit()

    return {"message": "Mail deleted successfully"}
