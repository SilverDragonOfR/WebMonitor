import os
from dotenv import load_dotenv
import requests
from celery import Celery
from app.notification import notify_status_change
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.crud import get_last_history_state, get_site, get_webhooks
from app.database import SiteStatusHistory, StatusType, SessionLocal
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, RetryError

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "10"))

# Retry attempted in case of error initially, before concluding that the site is really down
@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException), reraise=True)
def get_website_response(url, timeout):
    return requests.get(url, timeout=timeout)

celery = Celery("tasks", broker=REDIS_URL, broker_connection_retry_on_startup=True)

@celery.task
def check_website_status(site_id: int, database_optisation: bool = True):
    db: Session = SessionLocal()
    site = get_site(db, site_id)
    
    if not site:
        return

    webhooks = get_webhooks(db, site_id)
    
    start_time = datetime.now(timezone.utc)
    
    # Get the status information by HTTP request, on any error we just catch it
    try:
        response = get_website_response(site.url, timeout=DEFAULT_TIMEOUT_SECONDS)
        response_time = (datetime.now(timezone.utc) - start_time).microseconds // 1000
        new_status = StatusType.UP if response.status_code == site.expected_status_code else StatusType.DOWN
    except requests.RequestException:
        response_time = None
        new_status = StatusType.DOWN
        
    # Database optimisation.
    # If true, we do not store every check in database, potentially wasting and slowing the database
    # Only differing status is stored.
    if database_optisation:
        last_entry = get_last_history_state(db, site)

        if last_entry and last_entry.status != new_status:
            history_entry = SiteStatusHistory(site_id=site.id, status=new_status, response_time_ms=response_time, last_checked=start_time, last_status_change=last_entry.last_checked)
            db.add(history_entry)
            db.commit()
            notify_status_change(site, webhooks, history_entry)
    # If we do need this then store each status check as normal
    else:
        last_entry = get_last_history_state(db, site)
        
        # The logic here is that if previous check is similar status then previous_status_change is previous_status_change of previous
        # If not same then previous_status_change is the status time of previous check
        if last_entry and last_entry.status != new_status:
            previous_status_change = last_entry.last_checked
        else:
            previous_status_change = last_entry.last_status_change
            
        history_entry = SiteStatusHistory(site_id=site.id, status=new_status, response_time_ms=response_time, last_checked=start_time, last_status_change=previous_status_change)
        db.add(history_entry)
        db.commit()
        
        # Still notification will be sent only on differing status change
        if last_entry and last_entry.status != new_status:
            notify_status_change(site, webhooks, history_entry)

    # Reschedule the task to run again after the site's check interval
    check_website_status.apply_async((site.id, database_optisation), countdown=site.check_interval_seconds)

    db.close()