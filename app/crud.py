from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.database import Site, SiteStatusHistory, StatusType, Webhook
from app.models import SiteCreate, WebhookCreate
from app.notification import notify_status_change

def add_site(db: Session, site_data: SiteCreate):
    site = Site(url=str(site_data.url), name=site_data.name, check_interval_seconds=site_data.check_interval_seconds, expected_status_code=site_data.expected_status_code)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

def initial_history(db: Session, site: Site):
    current_time = datetime.now(timezone.utc)
    initial_history = SiteStatusHistory(site_id=site.id, status=StatusType.INITIAL, last_checked=current_time, last_status_change=current_time)
    db.add(initial_history)
    webhooks = get_webhooks(db, site.id)
    notify_status_change(site, webhooks, initial_history)
    db.commit()

def remove_site(db: Session, site_id: int):
    site = db.query(Site).filter(Site.id == site_id).first()
    if site:
        end_history(db, site)
        db.delete(site)
        db.commit()
    return site

def end_history(db: Session, site: Site):
    current_time = datetime.now(timezone.utc)
    end_history = SiteStatusHistory(site_id=site.id, status=StatusType.END, last_checked=current_time, last_status_change=current_time)
    db.add(end_history)
    webhooks = get_webhooks(db, site.id)
    notify_status_change(site, webhooks, end_history)
    db.commit()
    
def get_site(db: Session, site_id: int):
    return db.query(Site).filter(Site.id == site_id).first()

def get_all_sites(db: Session):
    return db.query(Site).all()

def get_history(db: Session, site: Site):
    return db.query(SiteStatusHistory).filter(SiteStatusHistory.site_id == site.id).order_by(SiteStatusHistory.last_checked.desc()).all()

def get_last_history_state(db: Session, site: Site):
    return db.query(SiteStatusHistory).filter(SiteStatusHistory.site_id == site.id).order_by(SiteStatusHistory.last_checked.desc()).first()

def create_webhook(db: Session, webhook_data: WebhookCreate):
    webhook = Webhook(site_id=webhook_data.site_id, discord_webhook_url=webhook_data.discord_webhook_url)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook

def get_all_webhooks(db: Session):
    return db.query(Webhook).all()

def get_webhooks(db: Session, site_id: int):
    return db.query(Webhook).filter(Webhook.site_id == site_id).all()

def remove_webhook(db: Session, webhook_id: int):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook:
        db.delete(webhook)
        db.commit()
    return webhook