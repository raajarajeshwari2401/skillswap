"""Skill models module: SkillCategory, SkillOffer, and SkillRequest.
Implements OOP models with database constraints and serialization methods.
"""

from datetime import datetime, timezone
from app.extensions import db


class SkillCategory(db.Model):
    __tablename__ = "skill_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default="star")

    offers = db.relationship("SkillOffer", back_populates="category", cascade="all, delete-orphan")
    requests = db.relationship("SkillRequest", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SkillCategory {self.name}>"


class SkillOffer(db.Model):
    """An offer published by a student to teach or share a specific skill."""
    __tablename__ = "skill_offers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("skill_categories.id", ondelete="RESTRICT"), nullable=False)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    
    # Proficiency and mechanical metrics
    proficiency_level = db.Column(db.String(20), nullable=False, default="intermediate")  # beginner, intermediate, advanced
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    preparation_effort = db.Column(db.Integer, nullable=False, default=1)  # 1: Low, 2: Medium, 3: High
    interaction_mode = db.Column(db.String(20), nullable=False, default="hybrid")  # online, offline, hybrid
    location_details = db.Column(db.String(200), nullable=True, default="Campus / Video Call")
    
    # Automatically calculated by the Python SymPy scoring service
    difficulty = db.Column(db.String(30), nullable=False, default="Intermediate")
    suggested_points = db.Column(db.Float, nullable=False, default=30.0)
    scoring_breakdown_json = db.Column(db.Text, nullable=True)  # Stores JSON explanation of the formula
    
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="skill_offers")
    category = db.relationship("SkillCategory", back_populates="offers")
    exchanges = db.relationship("Exchange", back_populates="skill_offer", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.name if self.category else "General",
            "category_id": self.category_id,
            "user_id": self.user_id,
            "teacher_name": self.user.full_name if self.user else "Anonymous",
            "teacher_rating": self.user.get_average_rating() if self.user else 5.0,
            "proficiency_level": self.proficiency_level,
            "duration_minutes": self.duration_minutes,
            "preparation_effort": self.preparation_effort,
            "interaction_mode": self.interaction_mode,
            "difficulty": self.difficulty,
            "suggested_points": self.suggested_points,
            "location_details": self.location_details,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<SkillOffer {self.id}: {self.title} by User {self.user_id}>"


class SkillRequest(db.Model):
    """A request posted by a student wishing to learn a skill."""
    __tablename__ = "skill_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("skill_categories.id", ondelete="RESTRICT"), nullable=False)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    desired_level = db.Column(db.String(20), nullable=False, default="beginner")
    preferred_duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    interaction_mode = db.Column(db.String(20), nullable=False, default="hybrid")
    budget_points = db.Column(db.Float, nullable=False, default=30.0)
    is_open = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="skill_requests")
    category = db.relationship("SkillCategory", back_populates="requests")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.name if self.category else "General",
            "user_id": self.user_id,
            "learner_name": self.user.full_name if self.user else "Anonymous",
            "desired_level": self.desired_level,
            "preferred_duration_minutes": self.preferred_duration_minutes,
            "interaction_mode": self.interaction_mode,
            "budget_points": self.budget_points,
            "is_open": self.is_open,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<SkillRequest {self.id}: {self.title} by User {self.user_id}>"
