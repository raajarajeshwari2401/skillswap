"""ACID Wallet Service with Ledger Accounting and Escrow Mechanics.
Ensures point integrity, idempotency, concurrency safety, and audit traceability.
"""

from typing import Tuple, Optional
from datetime import datetime, timezone
import uuid
from app.extensions import db
from app.models.wallet import Wallet, PointTransaction
from app.models.exchange import Exchange, ExchangeStatus
from app.models.audit import AuditLog


class WalletTransactionError(Exception):
    """Raised when point verification or ledger consistency fails."""
    pass


class WalletService:
    """Enterprise-grade ACID wallet operations."""

    @staticmethod
    def create_wallet_for_user(user_id: int, initial_points: float = 50.0) -> Wallet:
        """Create a new user wallet with registration welcome grant."""
        wallet = Wallet(user_id=user_id, balance=initial_points, reserved_balance=0.0)
        db.session.add(wallet)
        db.session.flush()

        initial_tx = PointTransaction(
            wallet_id=wallet.id,
            amount=initial_points,
            transaction_type="welcome_bonus",
            balance_after=initial_points,
            description="Welcome to SkillSwap bonus points grant",
            idempotency_key=f"welcome-user-{user_id}",
        )
        db.session.add(initial_tx)
        return wallet

    @staticmethod
    def hold_reservation(exchange: Exchange) -> PointTransaction:
        """Lock points in escrow when a teacher accepts an exchange request."""
        learner_wallet = Wallet.query.filter_by(user_id=exchange.learner_id).with_for_update().first()
        if not learner_wallet:
            raise WalletTransactionError(f"Learner wallet {exchange.learner_id} not found.")

        cost = exchange.points_cost
        if not learner_wallet.can_afford(cost):
            raise WalletTransactionError(
                f"Insufficient available points ({learner_wallet.available_balance:.1f} available, {cost:.1f} required)."
            )

        # Idempotency guard
        idempotency_key = f"reserve-ex-{exchange.id}"
        existing_tx = PointTransaction.query.filter_by(idempotency_key=idempotency_key).first()
        if existing_tx:
            return existing_tx

        # Update escrow
        learner_wallet.reserved_balance = round(learner_wallet.reserved_balance + cost, 2)
        learner_wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            wallet_id=learner_wallet.id,
            amount=0.0,  # Total balance unchanged, escrow allocated
            transaction_type="hold_reservation",
            balance_after=learner_wallet.balance,
            description=f"Escrow lock of {cost:.1f} pts for Exchange #{exchange.id}",
            exchange_id=exchange.id,
            idempotency_key=idempotency_key,
        )
        db.session.add(tx)

        audit = AuditLog(
            user_id=exchange.learner_id,
            action="HOLD_RESERVATION",
            details=f"Reserved {cost:.1f} pts for Exchange #{exchange.id}",
        )
        db.session.add(audit)
        return tx

    @staticmethod
    def release_reservation(exchange: Exchange, reason: str = "Cancellation") -> Optional[PointTransaction]:
        """Release escrow reservation back to learner if exchange is cancelled/declined."""
        learner_wallet = Wallet.query.filter_by(user_id=exchange.learner_id).with_for_update().first()
        if not learner_wallet:
            return None

        cost = exchange.points_cost
        idempotency_key = f"release-ex-{exchange.id}"
        existing_tx = PointTransaction.query.filter_by(idempotency_key=idempotency_key).first()
        if existing_tx:
            return existing_tx

        # Release reserved funds safely
        learner_wallet.reserved_balance = max(0.0, round(learner_wallet.reserved_balance - cost, 2))
        learner_wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            wallet_id=learner_wallet.id,
            amount=0.0,
            transaction_type="release_reservation",
            balance_after=learner_wallet.balance,
            description=f"Released {cost:.1f} pts escrow reservation for Exchange #{exchange.id} ({reason})",
            exchange_id=exchange.id,
            idempotency_key=idempotency_key,
        )
        db.session.add(tx)

        audit = AuditLog(
            user_id=exchange.learner_id,
            action="RELEASE_RESERVATION",
            details=f"Released {cost:.1f} pts for Exchange #{exchange.id} ({reason})",
        )
        db.session.add(audit)
        return tx

    @staticmethod
    def settle_completed_exchange(exchange: Exchange) -> Tuple[PointTransaction, PointTransaction]:
        """Atomic settlement: debit learner, credit teacher, clear escrow, record ledger entries.
        Guarantees exactly-once execution via database state flag and unique idempotency keys.
        """
        if exchange.is_settled:
            raise WalletTransactionError(f"Exchange #{exchange.id} is already settled. Duplicate settlement rejected.")

        cost = exchange.points_cost

        # Lock both wallets in deterministic order to prevent deadlocks
        w1_id, w2_id = sorted([exchange.learner_id, exchange.teacher_id])
        wallets = {
            w.user_id: w
            for w in Wallet.query.filter(Wallet.user_id.in_([w1_id, w2_id])).with_for_update().all()
        }

        learner_wallet = wallets.get(exchange.learner_id)
        teacher_wallet = wallets.get(exchange.teacher_id)

        if not learner_wallet or not teacher_wallet:
            raise WalletTransactionError("One or both wallets could not be loaded for settlement.")

        if learner_wallet.balance < cost:
            raise WalletTransactionError(f"Learner has insufficient balance ({learner_wallet.balance} < {cost}).")

        # 1. Deduct from learner (clear reservation + debit total balance)
        learner_wallet.reserved_balance = max(0.0, round(learner_wallet.reserved_balance - cost, 2))
        learner_wallet.balance = round(learner_wallet.balance - cost, 2)
        learner_wallet.updated_at = datetime.now(timezone.utc)

        learner_tx = PointTransaction(
            wallet_id=learner_wallet.id,
            amount=-cost,
            transaction_type="session_payment",
            balance_after=learner_wallet.balance,
            description=f"Paid {cost:.1f} pts for completed Exchange #{exchange.id}",
            exchange_id=exchange.id,
            idempotency_key=f"settle-debit-ex-{exchange.id}",
        )
        db.session.add(learner_tx)

        # 2. Credit teacher
        teacher_wallet.balance = round(teacher_wallet.balance + cost, 2)
        teacher_wallet.updated_at = datetime.now(timezone.utc)

        teacher_tx = PointTransaction(
            wallet_id=teacher_wallet.id,
            amount=cost,
            transaction_type="session_earning",
            balance_after=teacher_wallet.balance,
            description=f"Earned {cost:.1f} pts teaching Exchange #{exchange.id}",
            exchange_id=exchange.id,
            idempotency_key=f"settle-credit-ex-{exchange.id}",
        )
        db.session.add(teacher_tx)

        # Mark exchange settled
        exchange.is_settled = True
        exchange.status = ExchangeStatus.COMPLETED.value
        exchange.updated_at = datetime.now(timezone.utc)

        audit = AuditLog(
            user_id=exchange.learner_id,
            action="SETTLE_EXCHANGE",
            details=f"Settled {cost:.1f} pts from User {exchange.learner_id} to User {exchange.teacher_id} for Exchange #{exchange.id}",
        )
        db.session.add(audit)

        return learner_tx, teacher_tx

    @staticmethod
    def admin_adjust_balance(user_id: int, delta: float, reason: str, admin_user_id: int) -> PointTransaction:
        """Administrative point credit or debit with explicit audit record."""
        wallet = Wallet.query.filter_by(user_id=user_id).with_for_update().first()
        if not wallet:
            raise WalletTransactionError(f"Wallet for user {user_id} not found.")

        new_balance = round(wallet.balance + delta, 2)
        if new_balance < 0:
            raise WalletTransactionError("Admin adjustment would cause negative balance.")

        wallet.balance = new_balance
        wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            wallet_id=wallet.id,
            amount=delta,
            transaction_type="admin_adjustment",
            balance_after=wallet.balance,
            description=f"Admin adjustment by #{admin_user_id}: {reason}",
            idempotency_key=f"admin-adj-{uuid.uuid4().hex[:12]}",
        )
        db.session.add(tx)

        audit = AuditLog(
            user_id=admin_user_id,
            action="ADMIN_BALANCE_ADJUST",
            details=f"Adjusted User #{user_id} balance by {delta:+.1f} pts. Reason: {reason}",
        )
        db.session.add(audit)
        return tx


wallet_service = WalletService()
