"""Routes package exporting all platform blueprints."""

from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.skills import skills_bp
from app.routes.exchanges import exchanges_bp
from app.routes.matching import matching_bp
from app.routes.wallet import wallet_bp
from app.routes.notifications import notifications_bp
from app.routes.profile import profile_bp
from app.routes.reviews import reviews_bp
from app.routes.admin import admin_bp

__all__ = [
    "main_bp",
    "auth_bp",
    "skills_bp",
    "exchanges_bp",
    "matching_bp",
    "wallet_bp",
    "notifications_bp",
    "profile_bp",
    "reviews_bp",
    "admin_bp",
]
