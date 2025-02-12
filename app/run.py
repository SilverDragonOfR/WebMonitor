import os
import sys
import signal
from app.background_worker import check_website_status
from app.crud import get_all_sites
from app.middleware import RateLimiterMiddleware
from app.models import DetailResponse
from fastapi import FastAPI
from app import sites
from dotenv import load_dotenv
from app.database import SessionLocal, Site, init_db

load_dotenv()

app = FastAPI()
app.include_router(sites.router)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", "20"))
OPTIMISATION = bool(os.getenv("RATE_WINDOW", True))

app.add_middleware(
    RateLimiterMiddleware, redis_url=REDIS_URL, limit=RATE_LIMIT, window=RATE_WINDOW
)

def receive_signal(signal_number, _):
    print(f'WebMonitor server shutting down... Signal: {signal.strsignal(signal_number)}')
    os.kill(os.getpid(), signal.SIGTERM)
    sys.exit(0)
    
def resume_monitoring():
    db = SessionLocal()
    existing_sites = get_all_sites(db)
    for site in existing_sites:
        check_website_status.apply_async((site.id, OPTIMISATION), countdown=site.check_interval_seconds)
    db.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    signal.signal(signal.SIGINT, receive_signal)
    resume_monitoring()

@app.get("/", response_model=DetailResponse)
def root():
    return {"detail": "WebMonitor is running"}