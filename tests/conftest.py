"""Pytest fixtures configuration.
Sets up an isolated in-memory SQLite database and test clients for integration testing.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.skill import SkillCategory
from app.services.wallet_service import wallet_service


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean transactional database session per test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def client(app, db_session):
    """A test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def user_a(db_session):
    """Fixture user A (Teacher)."""
    user = User(
        full_name="Alice Teacher",
        email="alice@test.edu",
        location="Campus North",
    )
    user.set_password("SecurePass123!")
    db_session.add(user)
    db_session.flush()
    wallet_service.create_wallet_for_user(user.id, initial_points=50.0)
    db_session.commit()
    return user


@pytest.fixture
def user_b(db_session):
    """Fixture user B (Learner)."""
    user = User(
        full_name="Bob Learner",
        email="bob@test.edu",
        location="Campus South",
    )
    user.set_password("SecurePass123!")
    db_session.add(user)
    db_session.flush()
    wallet_service.create_wallet_for_user(user.id, initial_points=50.0)
    db_session.commit()
    return user


@pytest.fixture
def category(db_session):
    """Fixture skill category."""
    cat = SkillCategory(
        name="Software Engineering",
        slug="software-engineering",
        description="Coding & Architecture",
    )
    db_session.add(cat)
    db_session.commit()
    return cat
