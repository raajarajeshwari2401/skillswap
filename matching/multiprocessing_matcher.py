"""Batch Parallel Matching Engine.
Academic Concept: Multiprocessing using Python's `concurrent.futures.ProcessPoolExecutor`
and `multiprocessing` module for CPU-bound batch compatibility calculations.
"""

import time
import os
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed


def _evaluate_single_pair(req: Dict[str, Any], off: Dict[str, Any]) -> Dict[str, Any]:
    """Pure top-level worker function (must be picklable for multiprocessing)."""
    # 1. Topic Relevance
    req_cat = req.get("category_id")
    off_cat = off.get("category_id")
    relevance = 30.0 if req_cat == off_cat else 8.0

    # Keyword check
    req_title = req.get("title", "").lower()
    off_text = f"{off.get('title', '')} {off.get('description', '')}".lower()
    words = [w for w in req_title.split() if len(w) > 3]
    hits = sum(1 for w in words if w in off_text)
    relevance = min(30.0, relevance + (hits * 3.0))

    # 2. Proficiency
    levels = {"beginner": 1, "intermediate": 2, "advanced": 3}
    t_val = levels.get(off.get("proficiency_level", "intermediate").lower(), 2)
    l_val = levels.get(req.get("desired_level", "beginner").lower(), 1)
    proficiency = 20.0 if t_val >= l_val else max(5.0, 20.0 - (l_val - t_val) * 10.0)

    # 3. Interaction Mode
    o_mode = off.get("interaction_mode", "hybrid").lower()
    r_mode = req.get("interaction_mode", "hybrid").lower()
    mode_score = 15.0 if (o_mode == r_mode or o_mode == "hybrid" or r_mode == "hybrid") else 0.0

    # 4. Affordability
    cost = off.get("suggested_points", 30.0)
    budget = req.get("budget_points", 50.0)
    affordability = 15.0 if cost <= budget else max(0.0, 15.0 - (cost - budget) * 0.5)

    # 5. Teacher Reputation
    rating = off.get("teacher_rating", 5.0)
    reputation = round((rating / 5.0) * 20.0, 1)

    total_score = round(min(100.0, relevance + proficiency + mode_score + affordability + reputation), 1)

    return {
        "offer_id": off.get("id"),
        "title": off.get("title"),
        "teacher_name": off.get("teacher_name", "Instructor"),
        "teacher_id": off.get("user_id"),
        "suggested_points": cost,
        "difficulty": off.get("difficulty", "Intermediate"),
        "compatibility_score": total_score,
        "score_breakdown": {
            "relevance": round(relevance, 1),
            "proficiency": round(proficiency, 1),
            "interaction_mode": round(mode_score, 1),
            "affordability": round(affordability, 1),
            "reputation": round(reputation, 1),
        },
        "pid": os.getpid(),  # Identifies the worker process ID for proof of multiprocessing
    }


def _worker_process_chunk(chunk_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Worker function that processes a chunk of candidate offers in parallel."""
    req = chunk_data["request"]
    candidates = chunk_data["candidates"]
    results = []
    for cand in candidates:
        # Exclude self-matches and inactive offers
        if cand.get("user_id") == req.get("user_id"):
            continue
        if not cand.get("is_active", True):
            continue
        results.append(_evaluate_single_pair(req, cand))
    return results


class MultiprocessingMatcher:
    """Manages parallel worker pools for large batch matching."""

    MIN_BATCH_FOR_PARALLEL = 8  # Only spawn processes when workload exceeds threshold

    @classmethod
    def match_batch(
        cls,
        request_dict: Dict[str, Any],
        candidate_offer_dicts: List[Dict[str, Any]],
        max_workers: int = 4,
        chunk_size: int = 10,
    ) -> Dict[str, Any]:
        """Compute matching results, using multiprocessing when dataset size warrants."""
        start_time = time.perf_counter()
        total_candidates = len(candidate_offer_dicts)
        used_multiprocessing = False
        worker_pids = set()
        matched_results: List[Dict[str, Any]] = []

        if total_candidates >= cls.MIN_BATCH_FOR_PARALLEL:
            used_multiprocessing = True
            # Split candidate dictionaries into chunks
            chunks = []
            for i in range(0, total_candidates, chunk_size):
                chunks.append({
                    "request": request_dict,
                    "candidates": candidate_offer_dicts[i:i + chunk_size],
                })

            worker_count = min(max_workers, max(1, len(chunks)))
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                futures = [executor.submit(_worker_process_chunk, c) for c in chunks]
                for future in as_completed(futures):
                    try:
                        batch_res = future.result()
                        for r in batch_res:
                            worker_pids.add(r.get("pid"))
                            matched_results.append(r)
                    except Exception as exc:
                        # Log and recover gracefully from worker process exceptions
                        print(f"[Multiprocessing Worker Error]: {exc}")
        else:
            # Sequential fallback for small batches to minimize process overhead
            chunk_data = {"request": request_dict, "candidates": candidate_offer_dicts}
            matched_results = _worker_process_chunk(chunk_data)
            worker_pids.add(os.getpid())

        # Sort ranked matches descending by compatibility score
        ranked_results = sorted(
            matched_results,
            key=lambda item: item["compatibility_score"],
            reverse=True,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "matches": ranked_results,
            "total_evaluated": len(matched_results),
            "used_multiprocessing": used_multiprocessing,
            "worker_pids": list(worker_pids),
            "execution_time_ms": elapsed_ms,
        }
