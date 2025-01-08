import logging

import typer
from sqlmodel import Session

from app.database import engine

from app.recommendations.recommendation_utils import RecommendationGenerator
from app.recommendations.underperforming_keywords import UnderperformingKeywordsRecommendation
from app.recommendations.new_keywords import NewKeywordsRecommendation
from app.recommendations.optimised_keywords import OptimisedKeywordsRecommendation

app = typer.Typer()


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RECOMMENDATION_TYPES = {
    "underperforming_keywords": UnderperformingKeywordsRecommendation,
    "new_keywords": NewKeywordsRecommendation,
    "optimised_keywords": OptimisedKeywordsRecommendation,
}


@app.command()
def generate(
    env: str = typer.Option(
        "dev",
        help="Environment mode: 'prod' for live data, 'dev' for test data",
        case_sensitive=False,
    ),
    rec_type: str = typer.Option(
        "underperforming_keywords",
        "--rec-type",
        "-r",
        help="Type of recommendation to generate (e.g., 'underperforming_keywords', 'new_keywords', 'optimised_keywords'). Alias: 'u' for 'underperforming_keywords', 'n' for 'new_keywords', 'o' for 'optimised_keywords'.",
        case_sensitive=False,
    ),
    num_campaigns: int = typer.Option(5, help="Number of campaigns to process"),
    ads_per_campaign: int = typer.Option(3, help="Number of ads per campaign to process"),
    keywords_per_ad: int = typer.Option(4, help="Number of keywords per ad to process"),
):
    """
    Generate Recommendations based on the specified type and environment.
    """

    env = env.lower()
    rec_type = rec_type.lower()

    if rec_type == "u":
        rec_type = "underperforming_keywords"
    elif rec_type == "n":
        rec_type = "new_keywords"
    elif rec_type == "o":
        rec_type = "optimised_keywords"

    env = env.lower()
    if env not in ["prod", "staging", "dev"]:
        env = "dev"

    if rec_type not in RECOMMENDATION_TYPES:
        available_types = ", ".join(RECOMMENDATION_TYPES.keys())
        logger.error(f"Invalid recommendation type. Available types: {available_types}")
        raise typer.Exit(code=1)

    with Session(engine) as session:
        recommendation_class = RECOMMENDATION_TYPES[rec_type]
        generator: RecommendationGenerator = recommendation_class(db=session, env=env)

        try:
            generator.generate(
                num_campaigns_to_process=num_campaigns,
                ads_per_campaign=ads_per_campaign,
                keywords_per_ad=keywords_per_ad,
            )
            logger.info("Recommendation generation completed successfully.")
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
