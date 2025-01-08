import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlmodel import Session

from app.ad.models import AdRecommendation
from app.keyword.models import Keyword, KeywordRecommendation
from app.campaign.models import CampaignRecommendation
from app.common_state_enums import RecommendationSeverity, RecommendationState, RecommendationType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RecommendationGenerator(ABC):
    def __init__(self, env: str, db: Session):
        self.db = db
        self.env = env

    @abstractmethod
    def generate(self, **kwargs):
        """
        Generate recommendations.
        :param kwargs: Additional keyword arguments.
        """
        pass


class KeywordPerformance(BaseModel):
    ad_group_id: str
    keyword_text: str
    clicks: int
    impressions: int
    cost: float
    conversions: float


def create_keyword_recommendation(
    db: Session,
    keyword: Keyword,
    description: str,
    rec_type: RecommendationType,
    severity: RecommendationSeverity = RecommendationSeverity.SUGGESTION,
) -> KeywordRecommendation:
    if not keyword.id:
        logger.error(f"Keyword {keyword.id} has no ID, skipping recommendation creation")
        raise ValueError("Keyword has no ID")
    keyword_recommendation = KeywordRecommendation(
        keyword_id=keyword.id,
        title="New Keyword",
        severity=severity,
        description=description,
        state=RecommendationState.PENDING,
        recommendation_type=rec_type,
        created_at=datetime.now(timezone.utc),
    )
    db.add(keyword_recommendation)
    db.commit()
    db.refresh(keyword_recommendation)
    return keyword_recommendation


def create_ad_recommendation(
    db: Session, ad_id: int, description: str, rec_type: RecommendationType
) -> AdRecommendation:
    ad_recommendation = AdRecommendation(
        ad_id=ad_id,
        title="New Keywords Recommendation",
        severity=RecommendationSeverity.FIX,
        description=description,
        state=RecommendationState.PENDING,
        recommendation_type=rec_type,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ad_recommendation)
    db.commit()
    db.refresh(ad_recommendation)
    return ad_recommendation


def create_campaign_recommendation(
    db: Session, campaign_id: int, description: str, rec_type: RecommendationType
) -> CampaignRecommendation:
    campaign_recommendation = CampaignRecommendation(
        campaign_id=campaign_id,
        title="New keywords recommendation",
        severity=RecommendationSeverity.SUGGESTION,
        description=description,
        state=RecommendationState.PENDING,
        recommendation_type=rec_type,
        created_at=datetime.now(timezone.utc),
    )
    db.add(campaign_recommendation)
    db.commit()
    db.refresh(campaign_recommendation)
    return campaign_recommendation
