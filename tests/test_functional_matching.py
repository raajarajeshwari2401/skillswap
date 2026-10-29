"""Tests for functional matching engine: map, filter, sorted, and lambdas."""

from app.models.skill import SkillOffer, SkillRequest
from app.services.matching_service import (
    calculate_category_relevance,
    calculate_proficiency_alignment,
    calculate_mode_compatibility,
    calculate_affordability_score,
    calculate_reputation_score,
    matching_service,
)


def test_pure_scoring_components():
    """Verify individual pure functions used in the functional pipeline."""
    # Proficiency alignment: teacher advanced (3) >= learner beginner (1) -> max 20 pts
    assert calculate_proficiency_alignment("advanced", "beginner") == 20.0
    # Teacher beginner (1) < learner advanced (3) -> penalized
    assert calculate_proficiency_alignment("beginner", "advanced") < 20.0

    # Interaction mode overlap
    assert calculate_mode_compatibility("online", "online") == 15.0
    assert calculate_mode_compatibility("hybrid", "offline") == 15.0
    assert calculate_mode_compatibility("offline", "online") == 0.0

    # Affordability
    assert calculate_affordability_score(30.0, 50.0, 100.0) == 15.0
    # Over budget but affordable with user balance
    assert calculate_affordability_score(40.0, 30.0, 50.0) == 10.0
    # Unaffordable (exceeds balance)
    assert calculate_affordability_score(60.0, 30.0, 50.0) == 0.0

    # Reputation (5 stars = 20 pts)
    assert calculate_reputation_score(5.0) == 20.0
    assert calculate_reputation_score(2.5) == 10.0


def test_functional_pipeline_ranking(db_session, user_a, user_b, category):
    """Test full ranking with filter(), map(), sorted(), and lambda."""
    # Create request by User B
    req = SkillRequest(
        user_id=user_b.id,
        category_id=category.id,
        title="Python Data Structures Tutoring",
        description="Looking for help with lists and graphs",
        desired_level="intermediate",
        budget_points=40.0,
        interaction_mode="online",
    )
    db_session.add(req)

    # Offer 1: High match (same category, online, within budget)
    offer_1 = SkillOffer(
        user_id=user_a.id,
        category_id=category.id,
        title="Python Data Structures and Algorithms",
        description="Tutoring in lists, trees, graphs",
        proficiency_level="advanced",
        duration_minutes=60,
        suggested_points=35.0,
        interaction_mode="online",
        is_active=True,
    )

    # Offer 2: Inactive offer (must be filtered out)
    offer_2 = SkillOffer(
        user_id=user_a.id,
        category_id=category.id,
        title="Inactive Course",
        description="Not available",
        is_active=False,
    )

    # Offer 3: Self-offer by user_b (must be filtered out)
    offer_3 = SkillOffer(
        user_id=user_b.id,
        category_id=category.id,
        title="User B Own Offer",
        description="Self offer",
        is_active=True,
    )

    db_session.add_all([offer_1, offer_2, offer_3])
    db_session.commit()

    candidates = [offer_1, offer_2, offer_3]
    ranked = matching_service.rank_candidates(req, candidates, user_b.wallet)

    # Only offer_1 should remain
    assert len(ranked) == 1
    best_match = ranked[0]
    assert best_match["offer_id"] == offer_1.id
    assert best_match["compatibility_score"] > 80.0
