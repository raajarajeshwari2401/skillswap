"""Wallet and PointTransaction models.
Implements ACID ledger architecture, point reservation (escrow), idempotency, and concurrency controls.
"""

from datetime import datetime, timezone
from app.extensions import db


class Wallet(db.Model):
    """User points wallet. Tracks total balance and escrowed/reserved balance."""
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    balance = db.Column(db.Float, default=50.0, nullable=False)
    reserved_balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="wallet")
    transactions = db.relationship(
        "PointTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="desc(PointTransaction.created_at)",
        lazy="dynamic",
    )

    @property
    def available_balance(self) -> float:
        """Net spending power available after deducting escrow reservations."""
        return max(0.0, round(self.balance - self.reserved_balance, 2))

    def can_afford(self, amount: float) -> bool:
        """Verify that user possesses adequate unreserved points."""
        return self.available_balance >= amount

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": round(self.balance, 2),
            "reserved_balance": round(self.reserved_balance, 2),
            "available_balance": round(self.available_balance, 2),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_id} balance={self.balance} reserved={self.reserved_balance}>"


class PointTransaction(db.Model):
    """Immutable ledger record for every point movement in the platform."""
    __tablename__ = "point_transactions"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(40), nullable=False, index=True)
    balance_after = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchanges.id", ondelete="SET NULL"), nullable=True, index=True)
    idempotency_key = db.Column(db.String(120), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    wallet = db.relationship("Wallet", back_populates="transactions")
    exchange = db.relationship("Exchange", back_populates="point_transactions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "wallet_id": self.wallet_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "balance_after": self.balance_after,
            "description": self.description,
            "exchange_id": self.exchange_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def __repr__(self) -> str:
        return f"<PointTransaction {self.id}: {self.transaction_type} {self.amount:+.1f} pts>"
