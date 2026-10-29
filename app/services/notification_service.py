"""Notification Service delivering persistent DB storage and real-time Socket.IO events.
"""

from typing import Optional
from app.extensions import db, socketio
from app.models.notification import Notification


class NotificationService:
    """Manages creation, database persistence, and real-time push of alerts."""

    @staticmethod
    def send_notification(
        user_id: int,
        title: str,
        message: str,
        link: Optional[str] = None,
        notification_type: str = "general",
    ) -> Notification:
        """Create a notification in the database and push an event via Socket.IO."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            notification_type=notification_type,
            is_read=False,
        )
        db.session.add(notification)
        db.session.commit()

        # Emit real-time event to the specific user's private socket room
        payload = notification.to_dict()
        try:
            socketio.emit(
                "new_notification",
                payload,
                room=f"user_{user_id}",
            )
        except Exception:
            # Fall back gracefully if socket subsystem is not connected in current context
            pass

        return notification


notification_service = NotificationService()
