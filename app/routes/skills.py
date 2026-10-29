"""Skills blueprint: Explore, create, and manage skill offers and skill requests."""

import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.skill import SkillCategory, SkillOffer, SkillRequest
from app.services.scoring_service import scoring_service

skills_bp = Blueprint("skills", __name__, url_prefix="/skills")


@skills_bp.route("/")
def explore():
    """Explore and search active skill offers with multiple filtering facets."""
    query_text = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    level = request.args.get("level", "").strip().lower()
    mode = request.args.get("mode", "").strip().lower()
    sort_by = request.args.get("sort", "newest")

    query = SkillOffer.query.filter_by(is_active=True)

    if query_text:
        query = query.filter(
            (SkillOffer.title.ilike(f"%{query_text}%")) |
            (SkillOffer.description.ilike(f"%{query_text}%"))
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if level in ["beginner", "intermediate", "advanced"]:
        query = query.filter_by(proficiency_level=level)

    if mode in ["online", "offline", "hybrid"]:
        query = query.filter_by(interaction_mode=mode)

    if sort_by == "points_asc":
        query = query.order_by(SkillOffer.suggested_points.asc())
    elif sort_by == "points_desc":
        query = query.order_by(SkillOffer.suggested_points.desc())
    elif sort_by == "duration":
        query = query.order_by(SkillOffer.duration_minutes.asc())
    else:  # newest
        query = query.order_by(SkillOffer.created_at.desc())

    offers = query.all()
    categories = SkillCategory.query.all()
    recent_requests = SkillRequest.query.filter_by(is_open=True).order_by(SkillRequest.created_at.desc()).limit(4).all()

    return render_template(
        "skills/explore.html",
        offers=offers,
        categories=categories,
        recent_requests=recent_requests,
        current_category=category_id,
        current_level=level,
        current_mode=mode,
        current_sort=sort_by,
        search_query=query_text,
    )


@skills_bp.route("/<int:offer_id>")
def detail(offer_id: int):
    """Inspect detailed skill offer including the SymPy formula breakdown."""
    offer = SkillOffer.query.get_or_404(offer_id)
    breakdown = {}
    if offer.scoring_breakdown_json:
        try:
            breakdown = json.loads(offer.scoring_breakdown_json)
        except Exception:
            pass

    # Similar offers in same category
    related_offers = (
        SkillOffer.query.filter(
            SkillOffer.category_id == offer.category_id,
            SkillOffer.id != offer.id,
            SkillOffer.is_active == True,
        )
        .limit(3)
        .all()
    )

    return render_template(
        "skills/detail.html",
        offer=offer,
        breakdown=breakdown,
        related_offers=related_offers,
    )


@skills_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_offer():
    """Publish a new skill offer with server-enforced SymPy point calculation."""
    categories = SkillCategory.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        proficiency_level = request.form.get("proficiency_level", "intermediate").strip().lower()
        duration_minutes = request.form.get("duration_minutes", 60, type=int)
        preparation_effort = request.form.get("preparation_effort", 1, type=int)
        interaction_mode = request.form.get("interaction_mode", "hybrid").strip().lower()
        location_details = request.form.get("location_details", "").strip()

        if not title or not description or not category_id:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template("skills/create_offer.html", categories=categories)

        # Academic SymPy Calculation: Users cannot set arbitrary point values
        points, difficulty, breakdown = scoring_service.calculate_points(
            duration_minutes=duration_minutes,
            proficiency_level=proficiency_level,
            prep_effort=preparation_effort,
        )

        offer = SkillOffer(
            user_id=current_user.id,
            category_id=category_id,
            title=title,
            description=description,
            proficiency_level=proficiency_level,
            duration_minutes=duration_minutes,
            preparation_effort=preparation_effort,
            interaction_mode=interaction_mode,
            location_details=location_details or "Campus / Online",
            difficulty=difficulty,
            suggested_points=points,
            scoring_breakdown_json=json.dumps(breakdown),
            is_active=True,
        )
        db.session.add(offer)
        db.session.commit()

        flash(f"Your skill '{title}' is published with calculated cost of {points} points ({difficulty})!", "success")
        return redirect(url_for("skills.detail", offer_id=offer.id))

    return render_template("skills/create_offer.html", categories=categories)


@skills_bp.route("/<int:offer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_offer(offer_id: int):
    """Modify existing skill offer. Only the original creator can edit."""
    offer = SkillOffer.query.get_or_404(offer_id)
    if offer.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    categories = SkillCategory.query.all()

    if request.method == "POST":
        offer.title = request.form.get("title", "").strip()
        offer.description = request.form.get("description", "").strip()
        offer.category_id = request.form.get("category_id", type=int)
        offer.proficiency_level = request.form.get("proficiency_level", "intermediate").strip().lower()
        offer.duration_minutes = request.form.get("duration_minutes", 60, type=int)
        offer.preparation_effort = request.form.get("preparation_effort", 1, type=int)
        offer.interaction_mode = request.form.get("interaction_mode", "hybrid").strip().lower()
        offer.location_details = request.form.get("location_details", "").strip()

        # Recalculate SymPy points
        points, difficulty, breakdown = scoring_service.calculate_points(
            duration_minutes=offer.duration_minutes,
            proficiency_level=offer.proficiency_level,
            prep_effort=offer.preparation_effort,
        )
        offer.suggested_points = points
        offer.difficulty = difficulty
        offer.scoring_breakdown_json = json.dumps(breakdown)

        db.session.commit()
        flash("Skill offer updated successfully.", "success")
        return redirect(url_for("skills.detail", offer_id=offer.id))

    return render_template("skills/create_offer.html", categories=categories, offer=offer, is_edit=True)


@skills_bp.route("/<int:offer_id>/toggle", methods=["POST"])
@login_required
def toggle_offer_status(offer_id: int):
    """Pause or unpause a skill offer."""
    offer = SkillOffer.query.get_or_404(offer_id)
    if offer.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    offer.is_active = not offer.is_active
    db.session.commit()
    status_str = "active" if offer.is_active else "paused"
    flash(f"Skill listing is now {status_str}.", "info")
    return redirect(request.referrer or url_for("skills.detail", offer_id=offer.id))


@skills_bp.route("/requests/create", methods=["GET", "POST"])
@login_required
def create_request():
    """Publish a request to learn a new skill from peers."""
    categories = SkillCategory.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        desired_level = request.form.get("desired_level", "beginner").strip().lower()
        duration = request.form.get("preferred_duration_minutes", 60, type=int)
        mode = request.form.get("interaction_mode", "hybrid").strip().lower()
        budget = request.form.get("budget_points", 30.0, type=float)

        if not title or not description or not category_id:
            flash("Please complete all required fields.", "danger")
            return render_template("skills/create_request.html", categories=categories)

        if budget > current_user.wallet.available_balance:
            flash(
                f"Your budget ({budget} pts) cannot exceed your available points ({current_user.wallet.available_balance} pts).",
                "warning",
            )
            return render_template("skills/create_request.html", categories=categories)

        req = SkillRequest(
            user_id=current_user.id,
            category_id=category_id,
            title=title,
            description=description,
            desired_level=desired_level,
            preferred_duration_minutes=duration,
            interaction_mode=mode,
            budget_points=budget,
            is_open=True,
        )
        db.session.add(req)
        db.session.commit()

        flash("Skill request posted! Check the Matching Recommendations tab for compatible teachers.", "success")
        return redirect(url_for("matching.recommendations", request_id=req.id))

    return render_template("skills/create_request.html", categories=categories)
