"""Main routes blueprint: landing page, public help, and user dashboard."""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from app.models.user import User
from app.models.skill import SkillCategory, SkillOffer, SkillRequest
from app.models.exchange import Exchange
from app.models.wallet import PointTransaction
from app.services.scoring_service import scoring_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page featuring live database metrics, featured skills, and platform rules."""
    # Compute live community statistics from actual database records
    total_users = User.query.count()
    total_skills = SkillOffer.query.filter_by(is_active=True).count()
    completed_sessions = Exchange.query.filter_by(status="completed").count()
    total_points_transferred = (
        PointTransaction.query.filter_by(transaction_type="session_earning")
        .with_entities(func.sum(PointTransaction.amount))
        .scalar()
        or 0.0
    )

    categories = SkillCategory.query.all()
    featured_offers = (
        SkillOffer.query.filter_by(is_active=True)
        .order_by(SkillOffer.created_at.desc())
        .limit(6)
        .all()
    )

    # SymPy point system examples for the landing explainer
    _, _, ex1 = scoring_service.calculate_points(30, "beginner", 1)
    _, _, ex2 = scoring_service.calculate_points(60, "intermediate", 1)
    _, _, ex3 = scoring_service.calculate_points(60, "advanced", 1)

    return render_template(
        "index.html",
        stats={
            "users": total_users,
            "skills": total_skills,
            "completed": completed_sessions,
            "points_transferred": round(total_points_transferred, 1),
        },
        categories=categories,
        featured_offers=featured_offers,
        examples=[ex1, ex2, ex3],
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Personalized user dashboard displaying balances, active exchanges, and alerts."""
    user = current_user
    wallet = user.wallet
    
    # Active exchanges as learner and teacher
    active_incoming = (
        user.received_exchanges
        .filter(Exchange.status.in_(["pending", "accepted", "scheduled"]))
        .order_by(Exchange.created_at.desc())
        .limit(5)
        .all()
    )
    active_outgoing = (
        user.sent_exchanges
        .filter(Exchange.status.in_(["pending", "accepted", "scheduled"]))
        .order_by(Exchange.created_at.desc())
        .limit(5)
        .all()
    )

    my_offers = user.skill_offers[:4]
    my_requests = user.skill_requests[:4]
    recent_notifications = user.notifications.limit(5).all()

    return render_template(
        "dashboard.html",
        wallet=wallet,
        active_incoming=active_incoming,
        active_outgoing=active_outgoing,
        my_offers=my_offers,
        my_requests=my_requests,
        notifications=recent_notifications,
    )


@main_bp.route("/help")
def help_center():
    """Help center and platform rules explainer."""
    return render_template("help.html")
