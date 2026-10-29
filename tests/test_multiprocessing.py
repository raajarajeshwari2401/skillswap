"""Tests for Python multiprocessing batch skill-matching workloads."""

from matching.multiprocessing_matcher import MultiprocessingMatcher


def test_sequential_fallback_for_small_batch():
    """Verify that batches below threshold do not incur process spawn overhead."""
    req = {
        "user_id": 999,
        "category_id": 1,
        "title": "Calculus II Integration",
        "desired_level": "intermediate",
        "interaction_mode": "hybrid",
        "budget_points": 40.0,
    }
    small_candidates = [
        {"id": 1, "user_id": 1, "category_id": 1, "title": "Calculus Tutoring", "proficiency_level": "intermediate", "interaction_mode": "hybrid", "suggested_points": 30.0, "is_active": True},
        {"id": 2, "user_id": 2, "category_id": 1, "title": "Math Homework Prep", "proficiency_level": "advanced", "interaction_mode": "hybrid", "suggested_points": 35.0, "is_active": True},
    ]

    result = MultiprocessingMatcher.match_batch(req, small_candidates)
    assert result["used_multiprocessing"] is False
    assert result["total_evaluated"] == 2
    assert len(result["matches"]) == 2


def test_parallel_multiprocessing_for_large_batch():
    """Verify that multiprocessing pool is genuinely engaged for eligible batch sizes."""
    req = {
        "user_id": 999,
        "category_id": 1,
        "title": "Machine Learning and Neural Networks in Python",
        "desired_level": "advanced",
        "interaction_mode": "online",
        "budget_points": 60.0,
    }

    # Generate 16 candidate offers to exceed MIN_BATCH_FOR_PARALLEL (8)
    large_candidates = []
    for i in range(16):
        large_candidates.append({
            "id": i + 100,
            "user_id": i + 1,  # different users
            "category_id": 1 if i % 2 == 0 else 2,
            "title": f"Skill Offering #{i}: Deep Learning in Python" if i % 2 == 0 else f"General Topic #{i}",
            "proficiency_level": "advanced" if i % 3 == 0 else "intermediate",
            "interaction_mode": "online" if i % 2 == 0 else "offline",
            "suggested_points": 30.0 + (i * 2.0),
            "teacher_rating": 4.5,
            "is_active": True,
        })

    result = MultiprocessingMatcher.match_batch(req, large_candidates, max_workers=2, chunk_size=4)

    assert result["used_multiprocessing"] is True
    assert result["total_evaluated"] == 16
    assert len(result["matches"]) == 16
    assert result["execution_time_ms"] > 0

    # Ensure results are sorted descending by score
    scores = [m["compatibility_score"] for m in result["matches"]]
    assert scores == sorted(scores, reverse=True)
