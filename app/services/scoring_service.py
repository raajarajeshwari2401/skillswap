"""SymPy-powered academic scoring engine for SkillSwap.
Calculates transparent, non-arbitrary difficulty tiers and suggested point allocations
using symbolic mathematics.
"""

from typing import Dict, Any, Tuple
import sympy as sp


class SympyScoringEngine:
    """Symbolic scoring model using SymPy symbols and expressions."""

    def __init__(self, base_rate: float = 10.0, max_prep_bonus: float = 15.0):
        self.base_rate_val = base_rate
        self.max_prep_bonus_val = max_prep_bonus

        # Define symbolic variables
        self.b = sp.Symbol("base_rate", positive=True)
        self.d = sp.Symbol("duration_minutes", positive=True)
        self.m = sp.Symbol("multiplier", positive=True)
        self.p = sp.Symbol("prep_effort", integer=True, positive=True)
        self.k = sp.Symbol("prep_bonus_unit", positive=True)

        # Symbolic Expression for base time units (30-minute intervals)
        self.time_units_expr = self.d / 30

        # Symbolic Base Session Cost
        self.base_cost_expr = self.time_units_expr * self.b * self.m

        # Symbolic Preparation Bonus (5 points per effort tier above baseline 1, capped)
        self.raw_prep_expr = sp.Max(0, (self.p - 1) * 5)
        self.prep_bonus_expr = sp.Min(self.raw_prep_expr, self.max_prep_bonus_val)

        # Total Symbolic Formula
        self.total_formula = self.base_cost_expr + self.prep_bonus_expr

    def get_multiplier_for_level(self, proficiency_level: str) -> float:
        """Map proficiency level to standard multiplier."""
        level = (proficiency_level or "intermediate").lower().strip()
        multipliers = {
            "beginner": 1.0,
            "intermediate": 1.5,
            "advanced": 2.0,
        }
        return multipliers.get(level, 1.5)

    def determine_difficulty(self, proficiency_level: str, duration_minutes: int, prep_effort: int) -> str:
        """Classify difficulty tier based on cognitive load and duration."""
        level = (proficiency_level or "intermediate").lower().strip()
        if level == "advanced" or (level == "intermediate" and (duration_minutes >= 90 or prep_effort >= 3)):
            return "Advanced"
        elif level == "intermediate" or (level == "beginner" and duration_minutes >= 90):
            return "Intermediate"
        return "Beginner"

    def calculate_points(
        self,
        duration_minutes: int,
        proficiency_level: str,
        prep_effort: int = 1,
    ) -> Tuple[float, str, Dict[str, Any]]:
        """Evaluate the symbolic scoring formula and return points, difficulty, and proof breakdown."""
        multiplier_val = self.get_multiplier_for_level(proficiency_level)
        prep_effort_val = max(1, min(prep_effort, 3))
        duration_val = max(15, duration_minutes)

        # Substitute symbolic values
        evaluated_base = float(
            self.base_cost_expr.subs({
                self.b: self.base_rate_val,
                self.d: duration_val,
                self.m: multiplier_val,
            }).evalf()
        )

        evaluated_bonus = float(
            self.prep_bonus_expr.subs({
                self.p: prep_effort_val,
            }).evalf()
        )

        total_points = round(evaluated_base + evaluated_bonus, 1)
        difficulty = self.determine_difficulty(proficiency_level, duration_val, prep_effort_val)

        breakdown = {
            "symbolic_formula": "Points = (Duration / 30) * BaseRate * Multiplier + Min(5 * (Prep - 1), MaxCap)",
            "duration_minutes": duration_val,
            "duration_units_30m": round(duration_val / 30, 2),
            "base_rate": self.base_rate_val,
            "proficiency_level": proficiency_level.capitalize(),
            "multiplier": multiplier_val,
            "base_points": evaluated_base,
            "preparation_tier": prep_effort_val,
            "preparation_bonus": evaluated_bonus,
            "total_calculated_points": total_points,
            "assigned_difficulty": difficulty,
        }

        return total_points, difficulty, breakdown


# Singleton instance for platform-wide calculations
scoring_service = SympyScoringEngine()
