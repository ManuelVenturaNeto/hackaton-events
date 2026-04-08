"""Service for calculating networking relevance scores.

Scoring methodology:
- Base score from expected audience size (0-30 points)
- Company diversity bonus (0-25 points)
- Category relevance (0-15 points)
- Format bonus for in-person events (0-10 points)
- Duration bonus (0-10 points)
- Brazil bonus for Brazil events (0-10 points)

Score range: 0-100
Higher scores indicate higher networking potential.
"""

import logging

from app.models.event import EventCreate

logger = logging.getLogger(__name__)

# Audience size thresholds for scoring
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
    """Calculates networking relevance scores for events.

    The score reflects how valuable an event is for professional
    networking based on audience size, company involvement, format,
    duration, and strategic relevance.

    All scoring fields are documented:
    - Audience size: authoritative when from official source, estimated otherwise
    - Company count: authoritative from event listings
    - Category/format/duration: authoritative from event data
    """

    def calculate_score(self, event: EventCreate) -> float:
        """Calculate the networking relevance score for an event.

        Args:
            event: The event to score.

        Returns:
            Score between 0 and 100.
        """
        score = 0.0

        # Audience size component (0-30)
        for threshold, points in AUDIENCE_TIERS:
            if event.expected_audience_size >= threshold:
                score += points
                break

        # Company diversity (0-25)
        num_companies = len(event.companies)
        if num_companies >= 10:
            score += 25
        elif num_companies >= 5:
            score += 20
        elif num_companies >= 3:
            score += 15
        elif num_companies >= 1:
            score += 10

        # Category relevance (0-15)
        category_scores = {
            "Technology": 15,
            "Banking / Financial": 13,
            "Business / Entrepreneurship": 12,
            "Medical / Healthcare": 11,
            "Agribusiness / Agriculture": 10,
        }
        score += category_scores.get(event.category.value, 10)

        # Format bonus (0-10)
        format_scores = {
            "in-person": 10,
            "hybrid": 8,
            "online": 4,
        }
        score += format_scores.get(event.format.value, 5)

        # Duration bonus (0-10)
        if event.duration_days >= 4:
            score += 10
        elif event.duration_days >= 3:
            score += 8
        elif event.duration_days >= 2:
            score += 6
        else:
            score += 3

        # Brazil strategic bonus (0-10)
        if event.location.country.lower() == "brazil":
            score += 10

        final_score = min(100.0, round(score, 1))
        logger.debug("Scored event '%s': %.1f", event.name, final_score)
        return final_score
