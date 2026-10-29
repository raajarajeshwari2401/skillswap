"""Tests for SymPy-powered academic scoring engine."""

import pytest
import sympy as sp
from app.services.scoring_service import SympyScoringEngine, scoring_service


def test_sympy_symbolic_expression_construction():
    """Verify SymPy symbols and algebraic formula definitions."""
    engine = SympyScoringEngine(base_rate=10.0, max_prep_bonus=15.0)

    # Check symbolic variables exist
    assert isinstance(engine.b, sp.Symbol)
    assert isinstance(engine.d, sp.Symbol)
    assert isinstance(engine.m, sp.Symbol)
    assert isinstance(engine.p, sp.Symbol)

    # Check symbolic time units simplification
    simplified_time = sp.simplify(engine.time_units_expr)
    assert simplified_time == engine.d / 30


def test_master_prompt_required_examples():
    """Verify the exact results mandated by the project prompt:
    1. Beginner, 30 minutes: 10 points
    2. Intermediate, 60 minutes: 30 points
    3. Advanced, 60 minutes: 40 points
    """
    # 1. Beginner, 30 minutes, prep=1
    pts1, diff1, breakdown1 = scoring_service.calculate_points(
        duration_minutes=30,
        proficiency_level="beginner",
        prep_effort=1,
    )
    assert pts1 == 10.0
    assert diff1 == "Beginner"
    assert breakdown1["multiplier"] == 1.0
    assert breakdown1["preparation_bonus"] == 0.0

    # 2. Intermediate, 60 minutes, prep=1
    pts2, diff2, breakdown2 = scoring_service.calculate_points(
        duration_minutes=60,
        proficiency_level="intermediate",
        prep_effort=1,
    )
    assert pts2 == 30.0
    assert diff2 == "Intermediate"
    assert breakdown2["multiplier"] == 1.5
    assert breakdown2["preparation_bonus"] == 0.0

    # 3. Advanced, 60 minutes, prep=1
    pts3, diff3, breakdown3 = scoring_service.calculate_points(
        duration_minutes=60,
        proficiency_level="advanced",
        prep_effort=1,
    )
    assert pts3 == 40.0
    assert diff3 == "Advanced"
    assert breakdown3["multiplier"] == 2.0
    assert breakdown3["preparation_bonus"] == 0.0


def test_preparation_bonus_and_cap():
    """Verify that preparation effort awards bonus points up to the configured cap."""
    # Prep tier 2 adds 5 points
    pts_p2, _, b2 = scoring_service.calculate_points(60, "intermediate", prep_effort=2)
    assert pts_p2 == 35.0
    assert b2["preparation_bonus"] == 5.0

    # Prep tier 3 adds 10 points
    pts_p3, _, b3 = scoring_service.calculate_points(60, "intermediate", prep_effort=3)
    assert pts_p3 == 40.0
    assert b3["preparation_bonus"] == 10.0


def test_difficulty_classification():
    """Verify automatic classification of difficulty based on level and duration."""
    assert scoring_service.determine_difficulty("beginner", 30, 1) == "Beginner"
    assert scoring_service.determine_difficulty("intermediate", 60, 1) == "Intermediate"
    assert scoring_service.determine_difficulty("advanced", 60, 1) == "Advanced"
    assert scoring_service.determine_difficulty("beginner", 90, 1) == "Intermediate"
