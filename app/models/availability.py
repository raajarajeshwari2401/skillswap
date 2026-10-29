"""AvailabilitySlot model for teacher and learner scheduling."""

from datetime import datetime, timezone
from app.extensions import db


class AvailabilitySlot(db.Model):
    __tablename__ = "availability_slots"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = db.Column(db.String(15), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.String(10), nullable=False)    # e.g. "09:00"
    end_time = db.Column(db.String(10), nullable=False)      # e.g. "12:00"
    is_recurring = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="availability_slots")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    def __repr__(self) -> str:
        return f"<AvailabilitySlot User {self.user_id} {self.day_of_week} {self.start_time}-{self.end_time}>"
