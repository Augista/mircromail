from fastapi import FastAPI

from config import settings


app = FastAPI(
    title="MicroMail Mail Service",
    description="Mail service responsible for delivering and managing mails",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return { "status": "healthy" }

@app.get("/mail")
async def retrieve_emails():
    return

@app.post("/mail")
async def send_mail():
    return

@app.get("/mail/{mail_id}")
async def get_mail(mail_id: str):
    return

@app.patch("/mail/{mail_id}")
async def update_mail(mail_id: str):
    return

@app.delete("/mail/{mail_id}")
async def delete_mail(mail_id: str):
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.DELIVERY_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
