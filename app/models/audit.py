"""AuditLog model for recording sensitive system and wallet operations."""

from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    details = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def __repr__(self) -> str:
        return f"<AuditLog {self.id}: {self.action} by User {self.user_id}>"
