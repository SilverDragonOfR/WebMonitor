import os
from fastapi import APIRouter, Depends, Response, Security, status
from sqlalchemy.orm import Session
from app.background_worker import check_website_status
from app.database import Site, SessionLocal
from app.crud import create_webhook, get_all_webhooks, get_webhooks, initial_history, add_site, remove_site, get_site, get_all_sites, get_history, remove_webhook
from app.models import SiteCreate, SiteResponse, DetailResponse, SiteStatusHistoryResponse, WebhookCreate, WebhookResponse
from app.authetication import verify_credentials
from urllib.parse import urlparse

router = APIRouter()
OPTIMISATION = bool(os.getenv("RATE_WINDOW", True))

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
@router.get("/sites/{site_id}", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def get_each_site(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = get_site(db, site_id)
        if not site:
            raise Exception("Site not found")
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

@router.get("/sites", response_model=list[SiteResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(response: Response, db: Session = Depends(get_db)):
    try:
        sites = get_all_sites(db)
        return sites
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.get("/sites/{site_id}/history", response_model=list[SiteStatusHistoryResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_site_history(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = get_site(db, site_id)
        if not site:
            raise Exception("Site not found")
        history = get_history(db, site)
        return history
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.post("/sites", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def create_site(site: SiteCreate, response: Response, db: Session = Depends(get_db)):
    try:
        site = add_site(db, site)
        initial_history(db, site)
        check_website_status.apply_async((site.id, OPTIMISATION), countdown=site.check_interval_seconds)
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

@router.delete("/sites/{site_id}", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def delete_site(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = remove_site(db, site_id)
        if not site:
            raise Exception("Site not found")
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.get("/webhooks/{site_id}", response_model=list[WebhookResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        webhooks = get_webhooks(db, site_id)
        return webhooks
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.get("/webhooks", response_model=list[WebhookResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(response: Response, db: Session = Depends(get_db)):
    try:
        webhooks = get_all_webhooks(db)
        return webhooks
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.post("/webhooks", response_model=WebhookResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def create_site(webhook: WebhookCreate, response: Response, db: Session = Depends(get_db)):
    try:
        webhook = create_webhook(db, webhook)
        return webhook
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
@router.delete("/webhooks/{webhook_id}", response_model=WebhookResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def delete_site(webhook_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        webhook = remove_webhook(db, webhook_id)
        if not webhook:
            raise Exception("Webhook not found")
        return webhook
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}