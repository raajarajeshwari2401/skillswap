"""Reviews blueprint: Post feedback and calculate verified peer ratings."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.exchange import Exchange, ExchangeStatus
from app.models.review import Review
from app.services.notification_service import notification_service

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.route("/create/<int:exchange_id>", methods=["GET", "POST"])
@login_required
def create_review(exchange_id: int):
    """Submit 1-5 star review and testimonial following completed session."""
    exchange = Exchange.query.get_or_404(exchange_id)

    # Participant check
    if current_user.id not in [exchange.learner_id, exchange.teacher_id]:
        abort(403)

    # Verification check: only completed exchanges can be reviewed
    if exchange.status != ExchangeStatus.COMPLETED.value:
        flash("Reviews can only be submitted for completed sessions.", "warning")
        return redirect(url_for("exchanges.detail", exchange_id=exchange.id))

    # Duplicate review check
    existing = Review.query.filter_by(exchange_id=exchange.id, reviewer_id=current_user.id).first()
    if existing:
        flash("You have already submitted a review for this session.", "info")
        return redirect(url_for("exchanges.detail", exchange_id=exchange.id))

    # Determine reviewee
    reviewee_id = exchange.teacher_id if current_user.id == exchange.learner_id else exchange.learner_id
    target_role = "Instructor" if current_user.id == exchange.learner_id else "Learner"

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        if not rating or rating < 1 or rating > 5:
            flash("Please provide a rating between 1 and 5 stars.", "danger")
            return render_template("reviews/create.html", exchange=exchange, target_role=target_role)

        if not comment:
            flash("Please leave a brief comment on your experience.", "danger")
            return render_template("reviews/create.html", exchange=exchange, target_role=target_role)

        review = Review(
            exchange_id=exchange.id,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)
        db.session.commit()

        # Send notification to review recipient
        notification_service.send_notification(
            user_id=reviewee_id,
            title="New Review Received",
            message=f"{current_user.full_name} left you a {rating}-star review for '{exchange.skill_offer.title}'.",
            link=url_for("profile.view_profile", user_id=reviewee_id),
            notification_type="review",
        )

        flash("Thank you for your feedback!", "success")
        return redirect(url_for("exchanges.detail", exchange_id=exchange.id))

    return render_template("reviews/create.html", exchange=exchange, target_role=target_role)
