import os
from fastapi import APIRouter, Depends, Response, Security, status
from sqlalchemy.orm import Session
from app.background_worker import check_website_status
from app.database import Site, SessionLocal
from app.crud import create_webhook, get_all_webhooks, get_webhooks, initial_history, add_site, remove_site, get_site, get_all_sites, get_history, remove_webhook
from app.models import SiteCreate, SiteResponse, DetailResponse, SiteStatusHistoryResponse, WebhookCreate, WebhookResponse
from app.authetication import verify_credentials
from urllib.parse import urlparse

# Control flows here after starting of server
# All sites route are protected by Authentication
# On some error, we send HTTP 400 error with details
router = APIRouter()
OPTIMISATION = bool(os.getenv("OPTIMISATION", True))

# Dependency function to get a database session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
# Endpoint to get details of a specific site by ID
@router.get("/sites/{site_id}", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def get_each_site(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = get_site(db, site_id) # Fetch site from database by ID
        if not site:
            raise Exception("Site not found") # Raise exception if site is not found
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

# Endpoint to get a list of all sites
@router.get("/sites", response_model=list[SiteResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(response: Response, db: Session = Depends(get_db)):
    try:
        sites = get_all_sites(db) # Fetch all sites from the database
        return sites
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
# Endpoint to get the status history of a specific site
@router.get("/sites/{site_id}/history", response_model=list[SiteStatusHistoryResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_site_history(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = get_site(db, site_id) # Fetch site from database by ID
        if not site:
            raise Exception("Site not found") # Raise exception if site is not found
        history = get_history(db, site) # Fetch history for the site from the database
        return history
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
# Endpoint to create a new site
@router.post("/sites", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def create_site(site: SiteCreate, response: Response, db: Session = Depends(get_db)):
    try:
        site = add_site(db, site) # Add the new site to the database
        initial_history(db, site) # Initialize the site's history in the database
        check_website_status.apply_async((site.id, OPTIMISATION), countdown=site.check_interval_seconds) # Schedule background task to check website status
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

# Endpoint to delete a site by ID
@router.delete("/sites/{site_id}", response_model=SiteResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def delete_site(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        site = remove_site(db, site_id) # Remove the site from the database, Also removes the background process
        if not site:
            raise Exception("Site not found") # Raise exception if site is not found
        return site
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
# Endpoint to get webhooks for a specific site ID
@router.get("/webhooks/{site_id}", response_model=list[WebhookResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(site_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        webhooks = get_webhooks(db, site_id) # Fetch webhooks for a given site ID from the database
        return webhooks
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
    
# Endpoint to get a list of all webhooks
@router.get("/webhooks", response_model=list[WebhookResponse] | DetailResponse, dependencies=[Security(verify_credentials)])
def get_sites(response: Response, db: Session = Depends(get_db)):
    try:
        webhooks = get_all_webhooks(db) # Fetch all webhooks from the database
        return webhooks
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

# Endpoint to create a new webhook
@router.post("/webhooks", response_model=WebhookResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def create_site(webhook: WebhookCreate, response: Response, db: Session = Depends(get_db)):
    try:
        webhook = create_webhook(db, webhook) # Create a new webhook in the database
        return webhook
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}
   
# Endpoint to delete a webhook by ID 
@router.delete("/webhooks/{webhook_id}", response_model=WebhookResponse | DetailResponse, dependencies=[Security(verify_credentials)])
def delete_site(webhook_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        webhook = remove_webhook(db, webhook_id) # Remove the webhook from the database
        if not webhook:
            raise Exception("Webhook not found")
        return webhook
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}