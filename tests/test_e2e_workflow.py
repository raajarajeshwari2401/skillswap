"""End-to-End Workflow Integration Test.
Executes the exact 10-step sequence mandated in the project specification:
1. User A registers and publishes a skill.
2. User B registers and requests that skill.
3. The server calculates the difficulty and point cost.
4. User A accepts the request.
5. Notifications are sent and persisted.
6. The exchange is scheduled and completed.
7. Points are settled exactly once.
8. Eligible users submit reviews.
9. Both users log out and log in again.
10. Their accounts, balances, requests, notifications, and history remain intact.
"""

from app.models.user import User
from app.models.skill import SkillCategory, SkillOffer
from app.models.exchange import Exchange, ExchangeStatus
from app.models.review import Review
from app.models.notification import Notification
from app.services.scoring_service import scoring_service


def test_complete_10_step_e2e_lifecycle(client, db_session):
    # Ensure category exists
    cat = SkillCategory(name="Data Science", slug="data-science")
    db_session.add(cat)
    db_session.commit()

    # -------------------------------------------------------------
    # Step 1: User A registers and publishes a skill.
    # -------------------------------------------------------------
    res_reg_a = client.post(
        "/register",
        data={
            "full_name": "Alice Professor",
            "email": "alice.prof@college.edu",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "location": "North Science Quad",
        },
        follow_redirects=True,
    )
    assert res_reg_a.status_code == 200
    user_a = User.query.filter_by(email="alice.prof@college.edu").first()
    assert user_a is not None
    assert user_a.wallet.balance == 50.0  # Initial 50 pts

    # User A publishes a skill offer (Intermediate, 60 minutes, prep 1)
    res_create_offer = client.post(
        "/skills/create",
        data={
            "title": "Machine Learning Foundations with Scikit-Learn",
            "description": "Comprehensive tutorial on linear regression, classification, and cross-validation.",
            "category_id": cat.id,
            "proficiency_level": "intermediate",
            "duration_minutes": 60,
            "preparation_effort": 1,
            "interaction_mode": "online",
            "location_details": "Google Meet",
        },
        follow_redirects=True,
    )
    assert res_create_offer.status_code == 200
    offer = SkillOffer.query.filter_by(user_id=user_a.id).first()
    assert offer is not None

    # -------------------------------------------------------------
    # Step 3 (verified on offer creation): Server calculates difficulty and points
    # -------------------------------------------------------------
    assert offer.difficulty == "Intermediate"
    assert offer.suggested_points == 30.0  # (60/30)*10*1.5 = 30.0 points

    # User A logs out
    client.get("/logout", follow_redirects=True)

    # -------------------------------------------------------------
    # Step 2: User B registers and requests that skill.
    # -------------------------------------------------------------
    res_reg_b = client.post(
        "/register",
        data={
            "full_name": "Bob Student",
            "email": "bob.student@college.edu",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "location": "South Campus Dorms",
        },
        follow_redirects=True,
    )
    assert res_reg_b.status_code == 200
    user_b = User.query.filter_by(email="bob.student@college.edu").first()
    assert user_b.wallet.balance == 50.0

    # User B requests the session on User A's skill
    res_req = client.post(
        f"/exchanges/request/{offer.id}",
        data={"notes": "Need help preparing for midterms next Tuesday."},
        follow_redirects=True,
    )
    assert res_req.status_code == 200
    exchange = Exchange.query.filter_by(learner_id=user_b.id, teacher_id=user_a.id).first()
    assert exchange is not None
    assert exchange.status == ExchangeStatus.PENDING.value
    assert exchange.points_cost == 30.0

    # -------------------------------------------------------------
    # Step 5 (part 1): Notification sent and persisted to User A
    # -------------------------------------------------------------
    notif_a = Notification.query.filter_by(user_id=user_a.id).first()
    assert notif_a is not None
    assert "New Skill Request" in notif_a.title

    # User B logs out
    client.get("/logout", follow_redirects=True)

    # -------------------------------------------------------------
    # Step 4: User A logs in and accepts the request.
    # -------------------------------------------------------------
    client.post("/login", data={"email": "alice.prof@college.edu", "password": "Password123!"}, follow_redirects=True)
    res_accept = client.post(f"/exchanges/{exchange.id}/accept", follow_redirects=True)
    assert res_accept.status_code == 200

    db_session.refresh(exchange)
    db_session.refresh(user_b.wallet)
    assert exchange.status == ExchangeStatus.ACCEPTED.value

    # Escrow points are reserved in User B's wallet
    assert user_b.wallet.reserved_balance == 30.0
    assert user_b.wallet.available_balance == 20.0  # 50 - 30

    # -------------------------------------------------------------
    # Step 5 (part 2): Notification sent and persisted to User B
    # -------------------------------------------------------------
    notif_b = Notification.query.filter_by(user_id=user_b.id).first()
    assert notif_b is not None
    assert "Accepted" in notif_b.title

    # -------------------------------------------------------------
    # Step 6: The exchange is scheduled and completed.
    # -------------------------------------------------------------
    # Schedule
    res_sched = client.post(
        f"/exchanges/{exchange.id}/schedule",
        data={
            "scheduled_at": "2026-11-05T14:00",
            "meeting_location": "https://meet.google.com/abc-defg-hij",
        },
        follow_redirects=True,
    )
    assert res_sched.status_code == 200
    db_session.refresh(exchange)
    assert exchange.status == ExchangeStatus.SCHEDULED.value

    # Complete session
    res_complete = client.post(f"/exchanges/{exchange.id}/complete", follow_redirects=True)
    assert res_complete.status_code == 200

    # -------------------------------------------------------------
    # Step 7: Points are settled exactly once.
    # -------------------------------------------------------------
    db_session.refresh(exchange)
    db_session.refresh(user_a.wallet)
    db_session.refresh(user_b.wallet)

    assert exchange.is_settled is True
    assert exchange.status == ExchangeStatus.COMPLETED.value

    # User A earned 30 pts: 50 + 30 = 80.0
    assert user_a.wallet.balance == 80.0
    # User B paid 30 pts: 50 - 30 = 20.0; escrow cleared to 0.0
    assert user_b.wallet.balance == 20.0
    assert user_b.wallet.reserved_balance == 0.0
    assert user_b.wallet.available_balance == 20.0

    # User A logs out
    client.get("/logout", follow_redirects=True)

    # -------------------------------------------------------------
    # Step 8: Eligible users submit reviews.
    # -------------------------------------------------------------
    # User B logs in and leaves a 5-star review for User A
    client.post("/login", data={"email": "bob.student@college.edu", "password": "Password123!"}, follow_redirects=True)
    res_review = client.post(
        f"/reviews/create/{exchange.id}",
        data={
            "rating": 5,
            "comment": "Outstanding mentor! Explained scikit-learn pipelines with exceptional clarity.",
        },
        follow_redirects=True,
    )
    assert res_review.status_code == 200

    review = Review.query.filter_by(exchange_id=exchange.id, reviewer_id=user_b.id).first()
    assert review is not None
    assert review.rating == 5
    assert user_a.get_average_rating() == 5.0
    assert user_a.get_review_count() == 1

    # Prevent duplicate reviews for the same exchange
    res_dup_review = client.post(
        f"/reviews/create/{exchange.id}",
        data={"rating": 4, "comment": "Trying duplicate review"},
        follow_redirects=True,
    )
    assert b"already submitted a review" in res_dup_review.data

    # -------------------------------------------------------------
    # Step 9: Both users log out and log in again.
    # -------------------------------------------------------------
    client.get("/logout", follow_redirects=True)

    # User A relog
    res_relog_a = client.post("/login", data={"email": "alice.prof@college.edu", "password": "Password123!"}, follow_redirects=True)
    assert res_relog_a.status_code == 200
    client.get("/logout", follow_redirects=True)

    # User B relog
    res_relog_b = client.post("/login", data={"email": "bob.student@college.edu", "password": "Password123!"}, follow_redirects=True)
    assert res_relog_b.status_code == 200

    # -------------------------------------------------------------
    # Step 10: Accounts, balances, requests, notifications, and history remain intact.
    # -------------------------------------------------------------
    db_session.refresh(user_a)
    db_session.refresh(user_b)

    assert user_a.wallet.balance == 80.0
    assert user_b.wallet.balance == 20.0
    assert user_b.wallet.reserved_balance == 0.0

    assert user_a.skill_offers[0].title == "Machine Learning Foundations with Scikit-Learn"
    assert user_a.get_review_count() == 1
    assert user_a.get_completed_sessions_count() == 1

    assert user_a.notifications.count() >= 1
    assert user_b.notifications.count() >= 1

    # Verify transaction ledger records exist
    assert user_a.wallet.transactions.count() >= 2  # welcome_bonus + session_earning
    assert user_b.wallet.transactions.count() >= 3  # welcome_bonus + hold_reservation + session_payment
