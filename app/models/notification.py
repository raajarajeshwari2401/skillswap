"""Notification model for persistent real-time and offline alerts."""

from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    notification_type = db.Column(db.String(50), default="general", nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%b %d, %H:%M"),
        }

    def __repr__(self) -> str:
        return f"<Notification {self.id} for User {self.user_id}: {self.title}>"
