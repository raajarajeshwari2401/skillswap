"""Matching blueprint: Intelligent recommendation engine and live scoring APIs."""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.skill import SkillOffer, SkillRequest
from app.services.matching_service import matching_service
from app.services.scoring_service import scoring_service
from matching.multiprocessing_matcher import MultiprocessingMatcher

matching_bp = Blueprint("matching", __name__, url_prefix="/matching")


@matching_bp.route("/")
@login_required
def recommendations():
    """Evaluate and present ranked matches for student requests."""
    user_requests = current_user.skill_requests
    selected_request_id = request.args.get("request_id", type=int)

    selected_request = None
    if selected_request_id:
        selected_request = SkillRequest.query.get(selected_request_id)
    elif user_requests:
        selected_request = user_requests[0]

    ranked_matches = []
    stats_meta = {}

    if selected_request:
        candidate_offers = SkillOffer.query.filter_by(is_active=True).all()
        # If large pool, run through MultiprocessingMatcher to demonstrate multiprocessing
        if len(candidate_offers) >= MultiprocessingMatcher.MIN_BATCH_FOR_PARALLEL:
            req_dict = selected_request.to_dict()
            cand_dicts = [o.to_dict() for o in candidate_offers]
            batch_result = MultiprocessingMatcher.match_batch(req_dict, cand_dicts)
            
            # Map batch dicts back with offer objects for rich template rendering
            offer_map = {o.id: o for o in candidate_offers}
            for m in batch_result["matches"]:
                off = offer_map.get(m["offer_id"])
                if off:
                    ranked_matches.append({
                        "offer": off,
                        "compatibility_score": m["compatibility_score"],
                        "score_breakdown": m["score_breakdown"],
                        "reasons": [
                            f"Difficulty: {m['difficulty']}",
                            f"Points cost: {m['suggested_points']} pts",
                        ],
                    })
            stats_meta = {
                "used_multiprocessing": batch_result["used_multiprocessing"],
                "worker_pids": batch_result["worker_pids"],
                "execution_time_ms": batch_result["execution_time_ms"],
                "total_candidates": batch_result["total_evaluated"],
            }
        else:
            # Functional matching pipeline
            ranked_matches = matching_service.rank_candidates(
                request=selected_request,
                candidate_offers=candidate_offers,
                learner_wallet=current_user.wallet,
            )
            stats_meta = {
                "used_multiprocessing": False,
                "execution_mode": "Functional Pipeline (map/filter/sorted)",
                "total_candidates": len(ranked_matches),
            }

    return render_template(
        "matching/recommendations.html",
        user_requests=user_requests,
        selected_request=selected_request,
        matches=ranked_matches,
        meta=stats_meta,
    )


@matching_bp.route("/api/preview-points", methods=["GET"])
def preview_points():
    """Live JSON API using SymPy scoring engine as students adjust form sliders."""
    duration = request.args.get("duration", 60, type=int)
    level = request.args.get("level", "intermediate").strip().lower()
    prep = request.args.get("prep", 1, type=int)

    points, difficulty, breakdown = scoring_service.calculate_points(
        duration_minutes=duration,
        proficiency_level=level,
        prep_effort=prep,
    )

    return jsonify({
        "points": points,
        "difficulty": difficulty,
        "breakdown": breakdown,
    })
