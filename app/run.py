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

load_dotenv() # Loads environment variables from the .env file

app = FastAPI()
app.include_router(sites.router)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100")) # Rate Limit of per window per user
RATE_WINDOW = int(os.getenv("RATE_WINDOW", "20")) # Window Size
OPTIMISATION = bool(os.getenv("RATE_WINDOW", True)) # If True, we perform optimisation of database 

app.add_middleware(RateLimiterMiddleware, redis_url=REDIS_URL, limit=RATE_LIMIT, window=RATE_WINDOW) # Adding RateLimiterMiddleware for rate limiting

# Function to handle signals (CTRL+C) for graceful shutdown.
def receive_signal(signal_number, _):
    print(f'WebMonitor server shutting down... Signal: {signal.strsignal(signal_number)}')
    os.kill(os.getpid(), signal.SIGTERM)
    sys.exit(0)
    
# On starting of app, if there are any sites present in database, we resume monitoring for them
def resume_monitoring():
    db = SessionLocal()
    existing_sites = get_all_sites(db)
    for site in existing_sites: # Fetches all existing sites from the database.
        check_website_status.apply_async((site.id, OPTIMISATION), countdown=site.check_interval_seconds) # Schedules celery background worker for each
    db.close()

@app.on_event("startup")
async def startup_event(): # On Start of app, we start database and resume monitoring
    init_db()
    signal.signal(signal.SIGINT, receive_signal)
    resume_monitoring()

# Health check
@app.get("/", response_model=DetailResponse)
def root():
    return {"detail": "WebMonitor is running"}