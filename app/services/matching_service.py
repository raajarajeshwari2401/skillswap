"""Functional Programming Matching Engine.
Demonstrates functional paradigms in Python: pure functions, map(), filter(),
lambdas, and list/dict comprehensions to compute multidimensional compatibility.
"""

from typing import List, Dict, Any, Callable
from app.models.skill import SkillOffer, SkillRequest
from app.models.wallet import Wallet


def calculate_category_relevance(offer: SkillOffer, target_category_id: int, keywords: List[str]) -> float:
    """Pure function: calculate topic alignment (0 to 30 points)."""
    base = 30.0 if offer.category_id == target_category_id else 5.0
    # Functional comprehension checking keyword overlap in description/title
    if keywords:
        text = f"{offer.title} {offer.description}".lower()
        keyword_hits = sum(1 for kw in keywords if kw.lower() in text)
        bonus = min(10.0, keyword_hits * 3.0)
        return min(30.0, base + bonus)
    return base


def calculate_proficiency_alignment(offer_level: str, requested_level: str) -> float:
    """Pure function: score learning suitability (0 to 20 points)."""
    weights = {"beginner": 1, "intermediate": 2, "advanced": 3}
    t_val = weights.get((offer_level or "").lower(), 2)
    l_val = weights.get((requested_level or "").lower(), 1)

    # Teacher should ideally possess equal or higher proficiency than learner
    if t_val >= l_val:
        return 20.0
    else:
        return max(5.0, 20.0 - (l_val - t_val) * 10.0)


def calculate_mode_compatibility(offer_mode: str, preferred_mode: str) -> float:
    """Pure function: score interaction mode overlap (0 to 15 points)."""
    om = (offer_mode or "hybrid").lower()
    pm = (preferred_mode or "hybrid").lower()

    if om == pm or om == "hybrid" or pm == "hybrid":
        return 15.0
    return 0.0


def calculate_affordability_score(offer_points: float, budget_points: float, user_balance: float) -> float:
    """Pure function: assess point cost vs student budget and balance (0 to 15 points)."""
    if offer_points > user_balance:
        return 0.0
    if offer_points <= budget_points:
        return 15.0
    # Partial score if within 20% of budget
    diff = offer_points - budget_points
    return max(0.0, 15.0 - (diff * 0.5))


def calculate_reputation_score(rating: float) -> float:
    """Pure function: normalize 5-star rating into 0-20 score."""
    clamped_rating = max(1.0, min(5.0, rating or 5.0))
    return round((clamped_rating / 5.0) * 20.0, 1)


class FunctionalMatcher:
    """Engine orchestrating candidate filtering, mapping, and functional sorting."""

    @staticmethod
    def match_offer_to_request(
        offer: SkillOffer,
        request: SkillRequest,
        learner_wallet: Wallet = None,
    ) -> Dict[str, Any]:
        """Compute the composite compatibility record for a single pair."""
        available_balance = learner_wallet.available_balance if learner_wallet else 1000.0
        
        # Extract title keywords via comprehension
        raw_keywords = [w for w in request.title.split() if len(w) > 3]

        relevance = calculate_category_relevance(offer, request.category_id, raw_keywords)
        proficiency = calculate_proficiency_alignment(offer.proficiency_level, request.desired_level)
        mode = calculate_mode_compatibility(offer.interaction_mode, request.interaction_mode)
        affordability = calculate_affordability_score(offer.suggested_points, request.budget_points, available_balance)
        
        teacher_rating = offer.user.get_average_rating() if offer.user else 5.0
        reputation = calculate_reputation_score(teacher_rating)

        composite_score = round(min(100.0, relevance + proficiency + mode + affordability + reputation), 1)

        factor_reasons = []
        if relevance >= 25:
            factor_reasons.append("High topic relevance in requested category")
        if proficiency >= 18:
            factor_reasons.append(f"Instructor skill ({offer.proficiency_level}) meets/exceeds target ({request.desired_level})")
        if mode == 15.0:
            factor_reasons.append(f"Compatible interaction format ({offer.interaction_mode})")
        if affordability == 15.0:
            factor_reasons.append(f"Within student points budget ({offer.suggested_points} pts)")
        if reputation >= 18:
            factor_reasons.append(f"Top-rated instructor ({teacher_rating}/5.0 stars)")

        return {
            "offer": offer,
            "offer_id": offer.id,
            "teacher": offer.user,
            "teacher_name": offer.user.full_name if offer.user else "Instructor",
            "compatibility_score": composite_score,
            "score_breakdown": {
                "relevance": round(relevance, 1),
                "proficiency": round(proficiency, 1),
                "interaction_mode": round(mode, 1),
                "affordability": round(affordability, 1),
                "reputation": round(reputation, 1),
            },
            "reasons": factor_reasons,
        }

    @classmethod
    def rank_candidates(
        cls,
        request: SkillRequest,
        candidate_offers: List[SkillOffer],
        learner_wallet: Wallet = None,
    ) -> List[Dict[str, Any]]:
        """Rank candidates using Python functional primitives: filter(), map(), sorted(), lambda."""
        # 1. Functional filter: active offers, exclude requester's own offers
        active_unowned = list(
            filter(
                lambda off: off.is_active and off.user_id != request.user_id,
                candidate_offers,
            )
        )

        # 2. Functional map: evaluate compatibility record for each candidate
        scored_pairs = list(
            map(
                lambda off: cls.match_offer_to_request(off, request, learner_wallet),
                active_unowned,
            )
        )

        # 3. Functional sorted with lambda key: descending rank by composite score
        ranked = sorted(
            scored_pairs,
            key=lambda item: item["compatibility_score"],
            reverse=True,
        )

        return ranked


matching_service = FunctionalMatcher()
