from pydantic import BaseModel, HttpUrl
from datetime import datetime

class SiteCreate(BaseModel):
    url: HttpUrl
    name: str
    check_interval_seconds: int = 300
    expected_status_code: int = 200

class SiteResponse(SiteCreate):
    id: int

    class Config:
        from_attributes = True

class SiteStatusHistoryResponse(BaseModel):
    status: str
    response_time_ms: int | None
    last_checked: datetime
    last_status_change: datetime

    class Config:
        from_attributes = True
        
class WebhookCreate(BaseModel):
    site_id: int
    discord_webhook_url: str

class WebhookResponse(WebhookCreate):
    id: int

    class Config:
        from_attributes = True
        
class DetailResponse(BaseModel):
    detail: str
