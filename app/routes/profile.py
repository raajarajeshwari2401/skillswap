"""Profile blueprint: User profiles, public reputation, and availability management."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.availability import AvailabilitySlot

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/<int:user_id>")
def view_profile(user_id: int):
    """View public student profile with verified ratings, reviews, and listed offerings."""
    user = User.query.get_or_404(user_id)
    reviews = user.reviews_received.order_by(db.desc("created_at")).all()
    active_offers = user.skill_offers
    open_requests = user.skill_requests

    return render_template(
        "profile/view.html",
        profile_user=user,
        reviews=reviews,
        active_offers=active_offers,
        open_requests=open_requests,
        is_own_profile=(current_user.is_authenticated and current_user.id == user.id),
    )


@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Update profile bio, general location, and avatar settings."""
    user = current_user

    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.bio = request.form.get("bio", "").strip()
        user.location = request.form.get("location", "Campus / Remote").strip()
        user.avatar_url = request.form.get("avatar_url", "").strip()

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.view_profile", user_id=user.id))

    return render_template("profile/edit.html", user=user)


@profile_bp.route("/availability", methods=["GET", "POST"])
@login_required
def manage_availability():
    """Configure weekly availability slots for smooth peer session scheduling."""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            day = request.form.get("day_of_week")
            start = request.form.get("start_time")
            end = request.form.get("end_time")
            if day and start and end:
                slot = AvailabilitySlot(
                    user_id=current_user.id,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                )
                db.session.add(slot)
                db.session.commit()
                flash("Availability slot added.", "success")
        elif action == "delete":
            slot_id = request.form.get("slot_id", type=int)
            slot = AvailabilitySlot.query.get(slot_id)
            if slot and slot.user_id == current_user.id:
                db.session.delete(slot)
                db.session.commit()
                flash("Availability slot removed.", "info")

        return redirect(url_for("profile.manage_availability"))

    slots = current_user.availability_slots
    return render_template("profile/availability.html", slots=slots)
