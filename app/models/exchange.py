"""Exchange model implementing state machine transitions for skill sessions.
States: PENDING -> ACCEPTED -> SCHEDULED -> COMPLETED (or CANCELLED / REJECTED / DISPUTED).
"""

from datetime import datetime, timezone
from enum import Enum
from app.extensions import db


class ExchangeStatus(str, Enum):
    PENDING = "pending"          # Learner sent request, waiting for teacher approval
    ACCEPTED = "accepted"        # Teacher approved; points placed in escrow/reservation
    SCHEDULED = "scheduled"      # Specific time and venue/link confirmed
    COMPLETED = "completed"      # Both confirmed; points settled and escrow cleared
    CANCELLED = "cancelled"      # Either party cancelled before completion; escrow returned
    REJECTED = "rejected"        # Teacher declined the request
    DISPUTED = "disputed"        # Conflict reported to administrators


class Exchange(db.Model):
    __tablename__ = "exchanges"

    id = db.Column(db.Integer, primary_key=True)
    skill_offer_id = db.Column(db.Integer, db.ForeignKey("skill_offers.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    points_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default=ExchangeStatus.PENDING.value, nullable=False, index=True)
    
    # Message/notes from learner when requesting
    request_notes = db.Column(db.Text, nullable=True)
    
    # Scheduling details
    scheduled_at = db.Column(db.DateTime, nullable=True)
    meeting_location = db.Column(db.String(255), nullable=True)
    
    # Dual verification flags for fair settlement
    teacher_confirmed_completion = db.Column(db.Boolean, default=False, nullable=False)
    learner_confirmed_completion = db.Column(db.Boolean, default=False, nullable=False)
    
    # Idempotency guard: prevents double settlement
    is_settled = db.Column(db.Boolean, default=False, nullable=False, index=True)
    cancellation_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    skill_offer = db.relationship("SkillOffer", back_populates="exchanges")
    learner = db.relationship("User", foreign_keys=[learner_id], back_populates="sent_exchanges")
    teacher = db.relationship("User", foreign_keys=[teacher_id], back_populates="received_exchanges")
    point_transactions = db.relationship("PointTransaction", back_populates="exchange", lazy="dynamic")
    reviews = db.relationship("Review", back_populates="exchange", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="exchange", cascade="all, delete-orphan")

    def can_transition_to(self, new_status: str) -> bool:
        """State machine validator."""
        valid_transitions = {
            ExchangeStatus.PENDING.value: [
                ExchangeStatus.ACCEPTED.value,
                ExchangeStatus.REJECTED.value,
                ExchangeStatus.CANCELLED.value,
            ],
            ExchangeStatus.ACCEPTED.value: [
                ExchangeStatus.SCHEDULED.value,
                ExchangeStatus.COMPLETED.value,
                ExchangeStatus.CANCELLED.value,
                ExchangeStatus.DISPUTED.value,
            ],
            ExchangeStatus.SCHEDULED.value: [
                ExchangeStatus.COMPLETED.value,
                ExchangeStatus.CANCELLED.value,
                ExchangeStatus.DISPUTED.value,
            ],
            ExchangeStatus.COMPLETED.value: [
                ExchangeStatus.DISPUTED.value,
            ],
            ExchangeStatus.CANCELLED.value: [],
            ExchangeStatus.REJECTED.value: [],
            ExchangeStatus.DISPUTED.value: [
                ExchangeStatus.COMPLETED.value,
                ExchangeStatus.CANCELLED.value,
            ],
        }
        return new_status in valid_transitions.get(self.status, [])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "skill_title": self.skill_offer.title if self.skill_offer else "Unknown Skill",
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.full_name if self.teacher else "Instructor",
            "learner_id": self.learner_id,
            "learner_name": self.learner.full_name if self.learner else "Learner",
            "points_cost": self.points_cost,
            "status": self.status,
            "scheduled_at": self.scheduled_at.strftime("%Y-%m-%d %H:%M") if self.scheduled_at else None,
            "meeting_location": self.meeting_location,
            "is_settled": self.is_settled,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    def __repr__(self) -> str:
        return f"<Exchange {self.id} [{self.status}] Offer {self.skill_offer_id} Learner {self.learner_id}->Teacher {self.teacher_id}>"
