import os
import requests
import logging
from app.database import Site, SiteStatusHistory, StatusType, Webhook

DEFAULT_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "10"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_duration(duration_seconds: int):
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def send_discord_notification(webhook_url: str, message: str):
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error sending webhook to {webhook_url} : {e.strerror}")

def notify_status_change(site: Site, webhooks: list[Webhook], history_entry: SiteStatusHistory):
    url = site.url
    name = site.name if site.name else "Unknown"
    status = history_entry.status
    last_checked = history_entry.last_checked
    duration = format_duration((history_entry.last_checked - history_entry.last_status_change).total_seconds())
    
    message = ""

    if status == StatusType.INITIAL:
        message = f"🟡 **Website Monitoring Start**\n**Site:** {name} ({url})\n**Status:** INITIAL\n**Time:** {last_checked}"
    elif status == StatusType.UP:
        message = f"🟢 **Website Up Alert**\n**Site:** {name} ({url})\n**Status:** UP\n**Time:** {last_checked}\n**Downtime Duration:** {duration}"
    elif status == StatusType.DOWN:
        message = f"🔴 **Website Down Alert**\n**Site:** {name} ({url})\n**Status:** DOWN\n**Time:** {last_checked}\n**Uptime Duration:** {duration}"
    elif status == StatusType.END:
        message = f"🟡 **Website Monitoring End**\n**Site:** {name} ({url})\n**Status:** END\n**Time:** {last_checked}"

    for webhook in webhooks:
        send_discord_notification(webhook.discord_webhook_url, message)
