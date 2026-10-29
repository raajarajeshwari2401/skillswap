"""User model module implementing authentication and user profiles.
OOP Concept: Encapsulation of user state, password hashing, and profile properties.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True, default="Campus / Remote")
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    wallet = db.relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skill_offers = db.relationship("SkillOffer", back_populates="user", cascade="all, delete-orphan")
    skill_requests = db.relationship("SkillRequest", back_populates="user", cascade="all, delete-orphan")
    availability_slots = db.relationship("AvailabilitySlot", back_populates="user", cascade="all, delete-orphan")
    
    # Exchanges relationship as learner and teacher
    sent_exchanges = db.relationship(
        "Exchange",
        foreign_keys="Exchange.learner_id",
        back_populates="learner",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    received_exchanges = db.relationship(
        "Exchange",
        foreign_keys="Exchange.teacher_id",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Reviews
    reviews_written = db.relationship(
        "Review",
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    reviews_received = db.relationship(
        "Review",
        foreign_keys="Review.reviewee_id",
        back_populates="reviewee",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Notification.created_at)",
        lazy="dynamic",
    )

    def set_password(self, password: str) -> None:
        """Hash and securely store password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify candidate password against securely stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_average_rating(self) -> float:
        """Calculate arithmetic mean of received verified reviews."""
        reviews = self.reviews_received.all()
        if not reviews:
            return 5.0  # Default neutral/good reputation for new students
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_review_count(self) -> int:
        """Count total verified reviews received."""
        return self.reviews_received.count()

    def get_completed_sessions_count(self) -> int:
        """Count total completed sessions as teacher or learner."""
        completed_teacher = self.received_exchanges.filter_by(status="completed").count()
        completed_learner = self.sent_exchanges.filter_by(status="completed").count()
        return completed_teacher + completed_learner

    def to_dict(self) -> dict:
        """Serialize user summary for APIs and matching engine."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "location": self.location or "General Campus",
            "is_admin": self.is_admin,
            "rating": self.get_average_rating(),
            "review_count": self.get_review_count(),
            "completed_sessions": self.get_completed_sessions_count(),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email} ({self.full_name})>"
