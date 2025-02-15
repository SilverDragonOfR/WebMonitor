from pydantic import BaseModel, HttpUrl
from datetime import datetime

# These are the models used to encpsulate the data in HTTP cycle, not the way in which it is stored in database

# For creating a new website to monitor
class SiteCreate(BaseModel):
    url: HttpUrl
    name: str
    check_interval_seconds: int = 300
    expected_status_code: int = 200

# For representing a website's details in API responses
class SiteResponse(SiteCreate):
    id: int

    class Config:
        from_attributes = True

# For representing a website's status history entry in API responses
class SiteStatusHistoryResponse(BaseModel):
    status: str # UP, DOWN, INITIAL, END
    response_time_ms: int | None
    last_checked: datetime
    last_status_change: datetime

    class Config:
        from_attributes = True
    
# For creating a new webhook   
class WebhookCreate(BaseModel):
    site_id: int
    discord_webhook_url: str

# For representing a webhook's details in API responses
class WebhookResponse(WebhookCreate):
    id: int

    class Config:
        from_attributes = True
      
# For simple detail responses, used in error messages  
class DetailResponse(BaseModel):
    detail: str
