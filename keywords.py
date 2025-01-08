from typing import Optional, List, Tuple, Any
from enum import Enum
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient
from .errors import GoogleAdsErrorHandler

import re


def generate_keyword_ideas(
    client: GoogleAdsClient,
    googleads_account_id: str,
    page_url: str,
    keyword_texts=None,
    language_id: str | None = "1000",
):
    page_url = fix_url(page_url)

    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    # keyword_competition_level_enum = (
    #     client.enums.KeywordPlanCompetitionLevelEnum
    # )
    keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    language_rn = client.get_service("GoogleAdsService").language_constant_path(language_id)

    # Either keywords or a page_url are required to generate keyword ideas
    # so this raises an error if neither are provided.
    if not (keyword_texts or page_url):
        raise ValueError("At least one of keywords or page URL is required, " "but neither was specified.")

    # Only one of the fields "url_seed", "keyword_seed", or
    # "keyword_and_url_seed" can be set on the request, depending on whether
    # keywords, a page_url or both were passed to this function.
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = googleads_account_id
    request.language = language_rn
    request.include_adult_keywords = False
    request.keyword_plan_network = keyword_plan_network

    # To generate keyword ideas with only a page_url and no keywords we need
    # to initialize a UrlSeed object with the page_url as the "url" field.
    if not keyword_texts and page_url:
        request.url_seed.url = page_url

    # To generate keyword ideas with only a list of keywords and no page_url
    # we need to initialize a KeywordSeed object and set the "keywords" field
    # to be a list of StringValue objects.
    if keyword_texts and not page_url:
        request.keyword_seed.keywords.extend(keyword_texts)

    # To generate keyword ideas using both a list of keywords and a page_url we
    # need to initialize a KeywordAndUrlSeed object, setting both the "url" and
    # "keywords" fields.
    if keyword_texts and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keyword_texts)
    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(request=request)
    ideas = []

    for idea in keyword_ideas:
        if (
            hasattr(idea, "keyword_idea_metrics")
            and hasattr(idea.keyword_idea_metrics, "avg_monthly_searches")
            and hasattr(idea.keyword_idea_metrics, "competition_index")
            and hasattr(idea.keyword_idea_metrics, "low_top_of_page_bid")
            and hasattr(idea.keyword_idea_metrics, "high_top_of_page_bid")
        ):
            competition_value = idea.keyword_idea_metrics.competition
            ideas.append(
                {
                    "keyword": idea.text,
                    "competition": competition_value,
                    "average_monthly_searches": idea.keyword_idea_metrics.avg_monthly_searches,
                }
            )
    return ideas


def map_locations_ids_to_resource_names(client: GoogleAdsClient, location_ids: list[str]):
    """Converts a list of location IDs to resource names.

    Args:
        client: an initialized GoogleAdsClient instance.
        location_ids: a list of location ID strings.

    Returns:
        a list of resource name strings using the given location IDs.
    """
    build_resource_name = client.get_service("GeoTargetConstantService").geo_target_constant_path
    return [build_resource_name(location_id) for location_id in location_ids]


def fix_url(url: str):
    if not url.startswith("https://"):
        # Replace http:// with https:// or add https:// if it doesn't start with http:// or www.
        url = re.sub(r"^(http://)?", "https://", url)
    return url


class KeywordMatchType(str, Enum):
    EXACT = "EXACT"
    BROAD = "BROAD"
    PHRASE = "PHRASE"


class GoogleAdsKeywordIntegration:
    def __init__(
        self,
        client: Optional[Any] = None,
        googleads_account_id: Optional[str] = None,
        googleads_ad_group_id: Optional[str] = None,
        glitch_campaign_id: Optional[str] = None,
        keywords: Optional[List[Any]] = None,
        match_type: str = KeywordMatchType.BROAD,
    ):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.glitch_campaign_id = glitch_campaign_id
        self.keywords = keywords or []
        self.match_type = match_type
        self.googleads_ad_group_id = googleads_ad_group_id
        self.errors = []

    @property
    def ad_group_criterion_service(self):
        return self.client.get_service("AdGroupCriterionService")

    @property
    def ad_group_service(self):
        return self.client.get_service("AdGroupService")

    @property
    def googleads_service(self):
        return self.client.get_service("GoogleAdsService")

    def _create_base_criterion_operation(self, keyword_text: str, is_negative: bool = False) -> Any:
        """Create base ad group criterion operation with common settings."""
        operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = operation.create

        criterion.ad_group = self.ad_group_service.ad_group_path(
            customer_id=self.googleads_account_id, ad_group_id=self.googleads_ad_group_id
        )
        criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = keyword_text
        criterion.negative = is_negative

        # Set match type
        match_type_enum = self.client.enums.KeywordMatchTypeEnum
        match_type_mapping = {
            KeywordMatchType.EXACT: match_type_enum.EXACT,
            KeywordMatchType.BROAD: match_type_enum.BROAD,
            KeywordMatchType.PHRASE: match_type_enum.PHRASE,
        }
        criterion.keyword.match_type = match_type_mapping.get(self.match_type, match_type_enum.BROAD)

        return operation

    def _batch_mutate_keywords(
        self, operations: List[Any], is_negative: bool = False
    ) -> Tuple[Optional[Exception], List[Tuple]]:
        """Execute batch mutation of keywords and return results."""
        if not self.keywords or not self.client:
            return [], []

        try:
            response = self.ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.googleads_account_id, operations=operations
            )
            return self._process_mutation_response(response, is_negative)

        except GoogleAdsException as e:
            return (e, []) if not is_negative else []

    def _process_mutation_response(self, response: Any, is_negative: bool) -> Tuple[None, List[Tuple]]:
        """Process the mutation response and return formatted results."""
        ids = [keyword.id for keyword in self.keywords]
        googleads_ids = [result.resource_name for result in response.results]
        return None, list(zip(ids, googleads_ids))

    def add_keywords_to_googleads(self) -> Optional[Tuple[Optional[Exception], List[Tuple]]]:
        """Add multiple keywords to Google Ads."""
        if not self._validate_prerequisites():
            return None

        operations = [self._create_base_criterion_operation(keyword.text) for keyword in self.keywords]
        return self._batch_mutate_keywords(operations)

    def add_negative_keywords_to_googleads(self) -> Optional[Tuple[Optional[Exception], List[Tuple]]]:
        """Add multiple negative keywords to Google Ads."""
        if not self._validate_prerequisites():
            return None

        operations = [
            self._create_base_criterion_operation(keyword.text, is_negative=True) for keyword in self.keywords
        ]
        return self._batch_mutate_keywords(operations, is_negative=True)

    def _validate_prerequisites(self) -> bool:
        """Validate that required attributes are present."""
        return bool(self.keywords and self.client)

    def get_keywords_for_ad_group(self) -> List[str]:
        """Get all keyword resource names for the ad group."""
        query = self._build_keyword_query("ad_group_criterion.resource_name")
        return self._execute_keyword_query(query)

    def get_keywords_text_for_ad_group(self) -> List[str]:
        """Get all keyword texts for the ad group."""
        query = self._build_keyword_query("ad_group_criterion.keyword.text")
        return self._execute_keyword_query(query)

    def _build_keyword_query(self, select_field: str) -> str:
        """Build a query for keyword retrieval."""
        return f"""
            SELECT {select_field}
            FROM ad_group_criterion
            WHERE
                ad_group_criterion.type = 'KEYWORD'
                AND ad_group_criterion.status != 'REMOVED'
                AND ad_group.id = {self.googleads_ad_group_id}
        """

    def _execute_keyword_query(self, query: str) -> List[str]:
        """Execute a keyword query and return results."""
        response = self.googleads_service.search_stream(customer_id=self.googleads_account_id, query=query)

        keywords = []
        for batch in response:
            for row in batch.results:
                if "resource_name" in query:
                    keywords.append(row.ad_group_criterion.resource_name)
                else:
                    keywords.append(row.ad_group_criterion.keyword.text)
        return keywords

    def remove_keywords_from_googleads(self) -> None:
        """Remove all keywords from the ad group."""
        keywords = self.get_keywords_for_ad_group()
        if not keywords:
            return

        operations = [self._create_remove_operation(keyword) for keyword in keywords]

        self.ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=self.googleads_account_id, operations=operations
        )

    def _create_remove_operation(self, keyword: str) -> Any:
        """Create an operation to remove a keyword."""
        operation = self.client.get_type("AdGroupCriterionOperation")
        operation.remove = keyword
        return operation

    def add_error(self, ex: GoogleAdsException) -> None:
        """Add a Google Ads error to the error list."""
        error = GoogleAdsErrorHandler.create_error(
            ex=ex, class_name="Keyword", id=self.glitch_campaign_id, class_id=getattr(self, "keyword_id", None)
        )
        self.errors.append(error)
