from enum import Enum


class RecommendationSeverity(Enum):
    SUGGESTION = "suggestion"
    URGENT = "urgent"
    FIX = "fix"


class RecommendationState(Enum):
    PENDING = "pending"
    INSTANT_FIX_APPLIED = "instant fix applied"
    MARKED_RESOLVED = "marked resolved"
    MARKED_FAILED = "marked failed"
    MARKED_NOT_APPLICABLE = "marked not applicable"
    FAILED = "failed"


class RecommendationType(Enum):
    UNDERPERFORMING_KEYWORD = "underperforming_keyword"
    NEW_KEYWORD = "new_keyword"
