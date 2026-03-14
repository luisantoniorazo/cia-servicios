import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from models.enums import ActivityType, NotificationType

logger = logging.getLogger(__name__)

# This will be set by the main server
db = None

def set_database(database):
    global db
    db = database

async def log_activity(
    activity_type: ActivityType,
    module: str,
    action: str,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """Log an activity to the activity_logs collection"""
    if db is None:
        logger.warning("Database not initialized for activity logging")
        return
    
    log_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name,
        "activity_type": activity_type.value if hasattr(activity_type, 'value') else activity_type,
        "module": module,
        "action": action,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "details": details,
        "ip_address": ip_address,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.activity_logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Error logging activity: {e}")


async def create_notification(
    company_id: str,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    user_id: Optional[str] = None,
    link: Optional[str] = None
):
    """Create a notification for a user or all users in a company"""
    if db is None:
        logger.warning("Database not initialized for notifications")
        return
    
    notification = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type.value if hasattr(notification_type, 'value') else notification_type,
        "link": link,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.notifications.insert_one(notification)
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
