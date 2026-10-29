"""Exchanges blueprint: Handles the end-to-end lifecycle of skill exchanges.
State Machine: Pending -> Accepted (Escrow Held) -> Scheduled -> Completed (Settled) / Cancelled / Disputed.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.skill import SkillOffer
from app.models.exchange import Exchange, ExchangeStatus
from app.models.report import Report
from app.services.wallet_service import wallet_service, WalletTransactionError
from app.services.notification_service import notification_service

exchanges_bp = Blueprint("exchanges", __name__, url_prefix="/exchanges")


@exchanges_bp.route("/")
@login_required
def list_exchanges():
    """Display user's ongoing and historical skill sessions."""
    tab = request.args.get("tab", "all")
    
    learner_query = current_user.sent_exchanges
    teacher_query = current_user.received_exchanges

    if tab == "pending":
        incoming = teacher_query.filter_by(status=ExchangeStatus.PENDING.value).all()
        outgoing = learner_query.filter_by(status=ExchangeStatus.PENDING.value).all()
    elif tab == "active":
        incoming = teacher_query.filter(Exchange.status.in_([ExchangeStatus.ACCEPTED.value, ExchangeStatus.SCHEDULED.value])).all()
        outgoing = learner_query.filter(Exchange.status.in_([ExchangeStatus.ACCEPTED.value, ExchangeStatus.SCHEDULED.value])).all()
    elif tab == "completed":
        incoming = teacher_query.filter_by(status=ExchangeStatus.COMPLETED.value).all()
        outgoing = learner_query.filter_by(status=ExchangeStatus.COMPLETED.value).all()
    else:  # all
        incoming = teacher_query.order_by(Exchange.created_at.desc()).all()
        outgoing = learner_query.order_by(Exchange.created_at.desc()).all()

    return render_template(
        "exchanges/list.html",
        incoming=incoming,
        outgoing=outgoing,
        current_tab=tab,
    )


@exchanges_bp.route("/<int:exchange_id>")
@login_required
def detail(exchange_id: int):
    """View detailed exchange session, meeting coordinates, and action buttons."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.learner_id, exchange.teacher_id] and not current_user.is_admin:
        abort(403)

    is_teacher = current_user.id == exchange.teacher_id
    is_learner = current_user.id == exchange.learner_id
    has_reviewed = any(r.reviewer_id == current_user.id for r in exchange.reviews)

    return render_template(
        "exchanges/detail.html",
        exchange=exchange,
        is_teacher=is_teacher,
        is_learner=is_learner,
        has_reviewed=has_reviewed,
    )


@exchanges_bp.route("/request/<int:offer_id>", methods=["POST"])
@login_required
def create_exchange_request(offer_id: int):
    """Initiate exchange request from a learner to an instructor."""
    offer = SkillOffer.query.get_or_404(offer_id)

    if offer.user_id == current_user.id:
        flash("You cannot request your own skill listing.", "warning")
        return redirect(url_for("skills.detail", offer_id=offer.id))

    if not offer.is_active:
        flash("This skill listing is currently paused.", "warning")
        return redirect(url_for("skills.detail", offer_id=offer.id))

    # Verify learner possesses enough available points
    if not current_user.wallet.can_afford(offer.suggested_points):
        flash(
            f"You need at least {offer.suggested_points} available points (Current available: {current_user.wallet.available_balance}).",
            "danger",
        )
        return redirect(url_for("skills.detail", offer_id=offer.id))

    notes = request.form.get("notes", "").strip()

    exchange = Exchange(
        skill_offer_id=offer.id,
        learner_id=current_user.id,
        teacher_id=offer.user_id,
        points_cost=offer.suggested_points,
        status=ExchangeStatus.PENDING.value,
        request_notes=notes,
    )
    db.session.add(exchange)
    db.session.commit()

    # Real-time and persistent notification to teacher
    notification_service.send_notification(
        user_id=offer.user_id,
        title="New Skill Request Received",
        message=f"{current_user.full_name} requested your session on '{offer.title}'.",
        link=url_for("exchanges.detail", exchange_id=exchange.id),
        notification_type="exchange_request",
    )

    flash("Your request has been submitted to the instructor!", "success")
    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/accept", methods=["POST"])
@login_required
def accept(exchange_id: int):
    """Teacher accepts session: lock learner points into escrow reservation."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if exchange.teacher_id != current_user.id and not current_user.is_admin:
        abort(403)

    if not exchange.can_transition_to(ExchangeStatus.ACCEPTED.value):
        flash("This exchange cannot be accepted in its current state.", "warning")
        return redirect(url_for("exchanges.detail", exchange_id=exchange.id))

    try:
        # Hold escrow points in learner's wallet
        wallet_service.hold_reservation(exchange)
        exchange.status = ExchangeStatus.ACCEPTED.value
        db.session.commit()

        # Notify learner
        notification_service.send_notification(
            user_id=exchange.learner_id,
            title="Exchange Request Accepted!",
            message=f"{current_user.full_name} accepted your request for '{exchange.skill_offer.title}'. Please schedule your session.",
            link=url_for("exchanges.detail", exchange_id=exchange.id),
            notification_type="exchange_accepted",
        )
        flash("Exchange accepted. Points have been safely placed in escrow.", "success")
    except WalletTransactionError as exc:
        db.session.rollback()
        flash(f"Could not accept request: {str(exc)}", "danger")

    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/reject", methods=["POST"])
@login_required
def reject(exchange_id: int):
    """Teacher declines session request."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if exchange.teacher_id != current_user.id and not current_user.is_admin:
        abort(403)

    exchange.status = ExchangeStatus.REJECTED.value
    db.session.commit()

    notification_service.send_notification(
        user_id=exchange.learner_id,
        title="Exchange Request Declined",
        message=f"{current_user.full_name} was unable to accept your request for '{exchange.skill_offer.title}'.",
        link=url_for("exchanges.detail", exchange_id=exchange.id),
        notification_type="exchange_rejected",
    )
    flash("You have declined this exchange request.", "info")
    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/schedule", methods=["POST"])
@login_required
def schedule(exchange_id: int):
    """Set confirmed date, time, and venue or video link."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.learner_id, exchange.teacher_id]:
        abort(403)

    scheduled_date_str = request.form.get("scheduled_at", "").strip()
    meeting_location = request.form.get("meeting_location", "").strip()

    if scheduled_date_str:
        try:
            exchange.scheduled_at = datetime.fromisoformat(scheduled_date_str)
        except ValueError:
            pass

    if meeting_location:
        exchange.meeting_location = meeting_location

    exchange.status = ExchangeStatus.SCHEDULED.value
    db.session.commit()

    other_user_id = exchange.learner_id if current_user.id == exchange.teacher_id else exchange.teacher_id
    notification_service.send_notification(
        user_id=other_user_id,
        title="Session Scheduled",
        message=f"Meeting details updated for '{exchange.skill_offer.title}'.",
        link=url_for("exchanges.detail", exchange_id=exchange.id),
        notification_type="exchange_scheduled",
    )
    flash("Meeting details updated successfully.", "success")
    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/complete", methods=["POST"])
@login_required
def complete_session(exchange_id: int):
    """Confirm completion and trigger atomic points settlement."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.learner_id, exchange.teacher_id] and not current_user.is_admin:
        abort(403)

    exchange.teacher_confirmed_completion = True
    exchange.learner_confirmed_completion = True
    try:
        wallet_service.settle_completed_exchange(exchange)
        db.session.commit()

        # Notify teacher of earning
        notification_service.send_notification(
            user_id=exchange.teacher_id,
            title="Session Completed & Points Credited!",
            message=f"You earned {exchange.points_cost} points for teaching '{exchange.skill_offer.title}'.",
            link=url_for("wallet.overview"),
            notification_type="wallet_credit",
        )
        flash(f"Session completed! {exchange.points_cost} points transferred to instructor.", "success")
    except WalletTransactionError as exc:
        db.session.rollback()
        flash(f"Settlement failed: {str(exc)}", "danger")

    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/cancel", methods=["POST"])
@login_required
def cancel(exchange_id: int):
    """Cancel exchange and return any reserved escrow points to learner."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.learner_id, exchange.teacher_id] and not current_user.is_admin:
        abort(403)

    reason = request.form.get("reason", "Cancelled by user").strip()
    exchange.cancellation_reason = reason

    if exchange.status in [ExchangeStatus.ACCEPTED.value, ExchangeStatus.SCHEDULED.value]:
        wallet_service.release_reservation(exchange, reason=reason)

    exchange.status = ExchangeStatus.CANCELLED.value
    db.session.commit()

    other_user_id = exchange.learner_id if current_user.id == exchange.teacher_id else exchange.teacher_id
    notification_service.send_notification(
        user_id=other_user_id,
        title="Session Cancelled",
        message=f"The exchange for '{exchange.skill_offer.title}' was cancelled: {reason}",
        link=url_for("exchanges.detail", exchange_id=exchange.id),
        notification_type="exchange_cancelled",
    )
    flash("The exchange has been cancelled and any reserved points were released.", "info")
    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))


@exchanges_bp.route("/<int:exchange_id>/dispute", methods=["POST"])
@login_required
def dispute(exchange_id: int):
    """Report an issue and elevate to platform administrators."""
    exchange = Exchange.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.learner_id, exchange.teacher_id]:
        abort(403)

    reason = request.form.get("reason", "Dispute filed").strip()
    details = request.form.get("details", "").strip()

    reported_user_id = exchange.teacher_id if current_user.id == exchange.learner_id else exchange.learner_id
    report = Report(
        reporter_id=current_user.id,
        reported_user_id=reported_user_id,
        exchange_id=exchange.id,
        reason=reason,
        details=details,
        status="pending",
    )
    exchange.status = ExchangeStatus.DISPUTED.value
    db.session.add(report)
    db.session.commit()

    flash("Dispute submitted. An administrator will review the session records.", "warning")
    return redirect(url_for("exchanges.detail", exchange_id=exchange.id))
