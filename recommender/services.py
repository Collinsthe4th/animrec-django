"""Thin layer between the views and the shared ``animrec`` model.

The model is built once per process (it takes well under a second for the
200-title catalogue) and reused for every request.
"""

from __future__ import annotations

from functools import lru_cache

from animrec import AnimeRecommender


@lru_cache(maxsize=1)
def get_recommender() -> AnimeRecommender:
    return AnimeRecommender.from_csv()


def all_genres() -> list[str]:
    return get_recommender().genre_names


def clamp_k(raw: str | None, default: int = 10, low: int = 1, high: int = 20) -> int:
    """Parse the number of results from a query string and keep it in range."""
    try:
        value = int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))
