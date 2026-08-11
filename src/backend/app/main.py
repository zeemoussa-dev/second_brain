from fastapi import FastAPI

from app.api.email_poc_router import router as email_poc_router
from app.api.health_check_router import router as health_check_router
from app.scheduling.capture_scheduler import lifespan

app = FastAPI(title="Second Brain", lifespan=lifespan)

app.include_router(health_check_router)
app.include_router(email_poc_router)
