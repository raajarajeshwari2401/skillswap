"""Tests for ACID wallet operations, escrow holds, and settlement idempotency."""

import pytest
from app.models.skill import SkillOffer
from app.models.exchange import Exchange, ExchangeStatus
from app.models.wallet import PointTransaction
from app.services.wallet_service import wallet_service, WalletTransactionError


def test_escrow_hold_and_release(db_session, user_a, user_b, category):
    """Test point reservation into escrow and subsequent cancellation release."""
    offer = SkillOffer(
        user_id=user_a.id,
        category_id=category.id,
        title="Python Basics",
        description="Intro Python",
        proficiency_level="beginner",
        suggested_points=20.0,
        is_active=True,
    )
    db_session.add(offer)
    db_session.flush()

    exchange = Exchange(
        skill_offer_id=offer.id,
        teacher_id=user_a.id,
        learner_id=user_b.id,
        points_cost=20.0,
        status=ExchangeStatus.PENDING.value,
    )
    db_session.add(exchange)
    db_session.commit()

    # User B initial balance = 50.0, reserved = 0.0, available = 50.0
    assert user_b.wallet.available_balance == 50.0

    # 1. Hold reservation
    wallet_service.hold_reservation(exchange)
    db_session.commit()

    assert user_b.wallet.balance == 50.0
    assert user_b.wallet.reserved_balance == 20.0
    assert user_b.wallet.available_balance == 30.0

    # 2. Release reservation (cancellation)
    wallet_service.release_reservation(exchange, reason="User cancelled")
    db_session.commit()

    assert user_b.wallet.reserved_balance == 0.0
    assert user_b.wallet.available_balance == 50.0


def test_atomic_settlement_and_idempotency(db_session, user_a, user_b, category):
    """Test completion settlement: exactly once transfer with duplicate prevention."""
    offer = SkillOffer(
        user_id=user_a.id,
        category_id=category.id,
        title="Flask Mastery",
        description="Deep dive",
        proficiency_level="intermediate",
        suggested_points=30.0,
        is_active=True,
    )
    db_session.add(offer)
    db_session.flush()

    exchange = Exchange(
        skill_offer_id=offer.id,
        teacher_id=user_a.id,
        learner_id=user_b.id,
        points_cost=30.0,
        status=ExchangeStatus.ACCEPTED.value,
    )
    db_session.add(exchange)
    db_session.commit()

    # Hold escrow first
    wallet_service.hold_reservation(exchange)
    db_session.commit()

    assert user_a.wallet.balance == 50.0
    assert user_b.wallet.balance == 50.0
    assert user_b.wallet.reserved_balance == 30.0

    # Execute settlement
    wallet_service.settle_completed_exchange(exchange)
    db_session.commit()

    # Teacher gains 30 -> 80.0
    assert user_a.wallet.balance == 80.0
    # Learner spends 30 -> 20.0, escrow cleared to 0.0
    assert user_b.wallet.balance == 20.0
    assert user_b.wallet.reserved_balance == 0.0
    assert user_b.wallet.available_balance == 20.0
    assert exchange.is_settled is True

    # Attempt duplicate settlement: must raise WalletTransactionError
    with pytest.raises(WalletTransactionError) as exc_info:
        wallet_service.settle_completed_exchange(exchange)
    assert "already settled" in str(exc_info.value)

    # Balances must remain unchanged
    assert user_a.wallet.balance == 80.0
    assert user_b.wallet.balance == 20.0


def test_insufficient_balance_rejection(db_session, user_a, user_b, category):
    """Verify that a learner cannot reserve points beyond available funds."""
    offer = SkillOffer(
        user_id=user_a.id,
        category_id=category.id,
        title="Expensive 3-hour Bootcamp",
        description="Advanced topics",
        suggested_points=120.0,  # Learner only has 50.0
        is_active=True,
    )
    db_session.add(offer)
    db_session.flush()

    exchange = Exchange(
        skill_offer_id=offer.id,
        teacher_id=user_a.id,
        learner_id=user_b.id,
        points_cost=120.0,
        status=ExchangeStatus.PENDING.value,
    )
    db_session.add(exchange)
    db_session.commit()

    with pytest.raises(WalletTransactionError) as exc_info:
        wallet_service.hold_reservation(exchange)
    assert "Insufficient" in str(exc_info.value)
