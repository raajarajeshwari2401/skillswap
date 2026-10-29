"""Report and Dispute models for platform moderation and dispute resolution."""

from datetime import datetime, timezone
from app.extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchanges.id", ondelete="SET NULL"), nullable=True, index=True)
    
    reason = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="pending", nullable=False)  # pending, resolved, dismissed
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reporter = db.relationship("User", foreign_keys=[reporter_id])
    reported_user = db.relationship("User", foreign_keys=[reported_user_id])
    exchange = db.relationship("Exchange", back_populates="reports")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "reported_user_id": self.reported_user_id,
            "exchange_id": self.exchange_id,
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    def __repr__(self) -> str:
        return f"<Report {self.id}: {self.reason} [{self.status}]>"
