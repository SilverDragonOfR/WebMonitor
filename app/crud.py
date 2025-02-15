from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.database import Site, SiteStatusHistory, StatusType, Webhook
from app.models import SiteCreate, WebhookCreate
from app.notification import notify_status_change

# Function to add a new site to the database
def add_site(db: Session, site_data: SiteCreate):
    site = Site(url=str(site_data.url), name=site_data.name, check_interval_seconds=site_data.check_interval_seconds, expected_status_code=site_data.expected_status_code) # Create a Site object from the provided site_data
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

# Function to create the initial status history entry for a newly added site
def initial_history(db: Session, site: Site):
    current_time = datetime.now(timezone.utc) # Get the current time in UTC
    initial_history = SiteStatusHistory(site_id=site.id, status=StatusType.INITIAL, last_checked=current_time, last_status_change=current_time) # Create a SiteStatusHistory object to record the initial state of the site
    db.add(initial_history)
    webhooks = get_webhooks(db, site.id) # Retrieve all webhooks associated with this site
    notify_status_change(site, webhooks, initial_history) # Trigger the discord notification for the initial site status
    db.commit()

# Function to remove a site from the database by its ID
def remove_site(db: Session, site_id: int):
    site = db.query(Site).filter(Site.id == site_id).first() # Query the database to find the site with the given ID
    if site:
        end_history(db, site) # Create an "END" history entry before removing the site
        db.delete(site)
        db.commit()
    return site

# Function to create an "END" status history entry for a site, typically before site removal
def end_history(db: Session, site: Site):
    current_time = datetime.now(timezone.utc) # Get the current time in UTC
    end_history = SiteStatusHistory(site_id=site.id, status=StatusType.END, last_checked=current_time, last_status_change=current_time) # Create a SiteStatusHistory object to mark the end of monitoring for the site
    db.add(end_history) # Add the end history entry to the database sesssion
    webhooks = get_webhooks(db, site.id) # Retrieve all webhooks associated with this site
    notify_status_change(site, webhooks, end_history) # Trigger the discord notification for the initial site status
    db.commit()
    
# Function to retrieve a site from the database by its ID
def get_site(db: Session, site_id: int):
    return db.query(Site).filter(Site.id == site_id).first()

# Function to retrieve all sites from the database
def get_all_sites(db: Session):
    return db.query(Site).all()

# Function to retrieve the status history for a specific site
def get_history(db: Session, site: Site):
    return db.query(SiteStatusHistory).filter(SiteStatusHistory.site_id == site.id).order_by(SiteStatusHistory.last_checked.desc()).all()

# Function to retrieve the most recent status history entry for a specific site
def get_last_history_state(db: Session, site: Site):
    return db.query(SiteStatusHistory).filter(SiteStatusHistory.site_id == site.id).order_by(SiteStatusHistory.last_checked.desc()).first()

# Function to create a new webhook in the database
def create_webhook(db: Session, webhook_data: WebhookCreate):
    webhook = Webhook(site_id=webhook_data.site_id, discord_webhook_url=webhook_data.discord_webhook_url) # Create a Webhook object from the provided webhook_data
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook

# Function to retrieve all webhooks from the database
def get_all_webhooks(db: Session):
    return db.query(Webhook).all()

# Function to retrieve all webhooks associated with a specific site ID
def get_webhooks(db: Session, site_id: int):
    return db.query(Webhook).filter(Webhook.site_id == site_id).all()

# Function to remove a webhook from the database by its ID
def remove_webhook(db: Session, webhook_id: int): # Query the database to find the webhook with the given ID
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook:
        db.delete(webhook)
        db.commit()
    return webhook