"""Tests for user authentication, password hashing, and session management."""

from app.models.user import User


def test_registration_and_welcome_grant(client, db_session):
    """Test user registration flow and initial 50-point wallet creation."""
    response = client.post(
        "/register",
        data={
            "full_name": "Charlie Student",
            "email": "charlie@test.edu",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "location": "West Hall",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    user = User.query.filter_by(email="charlie@test.edu").first()
    assert user is not None
    assert user.full_name == "Charlie Student"
    assert user.check_password("Password123!") is True
    assert user.check_password("WrongPassword") is False

    # Check 50 welcome points in wallet
    assert user.wallet is not None
    assert user.wallet.balance == 50.0
    assert user.wallet.available_balance == 50.0


def test_login_flow(client, user_a):
    """Test login with valid and invalid credentials."""
    # Invalid password attempt
    bad_res = client.post(
        "/login",
        data={"email": user_a.email, "password": "WrongPassword!"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in bad_res.data

    # Valid password attempt
    good_res = client.post(
        "/login",
        data={"email": user_a.email, "password": "SecurePass123!"},
        follow_redirects=True,
    )
    assert good_res.status_code == 200
    assert b"Dashboard" in good_res.data


def test_protected_routes(client):
    """Verify unauthorized access redirects to login."""
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
