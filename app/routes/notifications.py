"""Notifications blueprint: Manage real-time and archived alerts."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@login_required
def center():
    """View full notification center."""
    notifications = current_user.notifications.all()
    return render_template("notifications/index.html", notifications=notifications)


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all unread notifications as read."""
    current_user.notifications.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "info")
    return redirect(url_for("notifications.center"))


@notifications_bp.route("/<int:notification_id>/read", methods=["GET", "POST"])
@login_required
def mark_read(notification_id: int):
    """Mark specific notification as read and navigate to associated link."""
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        return redirect(url_for("notifications.center"))

    notif.is_read = True
    db.session.commit()

    if notif.link:
        return redirect(notif.link)
    return redirect(url_for("notifications.center"))
