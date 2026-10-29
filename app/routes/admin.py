"""Admin blueprint: Platform moderation, dispute handling, audit ledger, and user controls."""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.skill import SkillOffer, SkillCategory
from app.models.exchange import Exchange
from app.models.wallet import Wallet, PointTransaction
from app.models.report import Report
from app.models.audit import AuditLog
from app.services.wallet_service import wallet_service, WalletTransactionError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to enforce admin privileges."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Administrator privileges required.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/")
@admin_required
def dashboard():
    """Main administrative dashboard with platform telemetry."""
    users_count = User.query.count()
    skills_count = SkillOffer.query.count()
    exchanges_count = Exchange.query.count()
    disputes_count = Report.query.filter_by(status="pending").count()
    total_points = db.session.query(func.sum(Wallet.balance)).scalar() or 0.0

    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    pending_disputes = Report.query.filter_by(status="pending").order_by(Report.created_at.desc()).all()
    recent_transactions = PointTransaction.query.order_by(PointTransaction.created_at.desc()).limit(15).all()

    return render_template(
        "admin/dashboard.html",
        stats={
            "users": users_count,
            "skills": skills_count,
            "exchanges": exchanges_count,
            "disputes": disputes_count,
            "total_points": round(total_points, 1),
        },
        recent_users=recent_users,
        pending_disputes=pending_disputes,
        recent_transactions=recent_transactions,
    )


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id: int):
    """Activate or suspend student account."""
    if user_id == current_user.id:
        flash("You cannot suspend your own administrative account.", "warning")
        return redirect(url_for("admin.dashboard"))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    action_str = "activated" if user.is_active else "suspended"
    flash(f"User '{user.full_name}' has been {action_str}.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/disputes/<int:report_id>/resolve", methods=["POST"])
@admin_required
def resolve_dispute(report_id: int):
    """Resolve or dismiss open report."""
    report = Report.query.get_or_404(report_id)
    resolution = request.form.get("resolution", "resolved")
    admin_notes = request.form.get("admin_notes", "").strip()

    report.status = resolution
    report.admin_notes = admin_notes
    db.session.commit()

    flash(f"Dispute #{report.id} marked as {resolution}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/adjust-points", methods=["POST"])
@admin_required
def adjust_points():
    """Manual administrative point modification with full audit trace."""
    user_id = request.form.get("user_id", type=int)
    delta = request.form.get("delta", type=float)
    reason = request.form.get("reason", "Admin manual adjustment").strip()

    if not user_id or delta is None:
        flash("Invalid user or adjustment value.", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        wallet_service.admin_adjust_balance(user_id, delta, reason, current_user.id)
        db.session.commit()
        flash(f"Successfully adjusted User #{user_id} balance by {delta:+.1f} points.", "success")
    except WalletTransactionError as exc:
        db.session.rollback()
        flash(f"Adjustment failed: {str(exc)}", "danger")

    return redirect(url_for("admin.dashboard"))
