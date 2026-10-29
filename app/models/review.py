"""Review model for verified feedback following completed exchanges."""

from datetime import datetime, timezone
from app.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchanges.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("exchange_id", "reviewer_id", name="uq_exchange_reviewer"),
    )

    exchange = db.relationship("Exchange", back_populates="reviews")
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_written")
    reviewee = db.relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "exchange_id": self.exchange_id,
            "reviewer_name": self.reviewer.full_name if self.reviewer else "Anonymous",
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%b %d, %Y"),
        }

    def __repr__(self) -> str:
        return f"<Review {self.id}: Exchange {self.exchange_id} Rating {self.rating} by {self.reviewer_id}>"
