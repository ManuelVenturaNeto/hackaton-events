"""Service for calculating networking relevance scores."""

import logging

from app.models.event import EventCreate

logger = logging.getLogger(__name__)

AUDIENCE_TIERS = [
    (100000, 30),
    (50000, 27),
    (20000, 24),
    (10000, 20),
    (5000, 15),
    (1000, 10),
    (0, 5),
]


class ScoringService:
    """Calculates networking relevance scores for events (0-100)."""

    def calculate_score(self, event: EventCreate) -> float:
        score = 0.0

        for threshold, points in AUDIENCE_TIERS:
            if event.expected_audience_size >= threshold:
                score += points
                break

        num_companies = len(event.companies)
        if num_companies >= 10:
            score += 25
        elif num_companies >= 5:
            score += 20
        elif num_companies >= 3:
            score += 15
        elif num_companies >= 1:
            score += 10

        category_scores = {
            "Technology": 15,
            "Banking / Financial": 13,
            "Business / Entrepreneurship": 12,
            "Medical / Healthcare": 11,
            "Agribusiness / Agriculture": 10,
        }
        score += category_scores.get(event.category.value, 10)

        format_scores = {
            "in-person": 10,
            "hybrid": 8,
            "online": 4,
        }
        score += format_scores.get(event.format.value, 5)

        if event.duration_days >= 4:
            score += 10
        elif event.duration_days >= 3:
            score += 8
        elif event.duration_days >= 2:
            score += 6
        else:
            score += 3

        if event.location.country.lower() == "brazil":
            score += 10

        return min(100.0, round(score, 1))
