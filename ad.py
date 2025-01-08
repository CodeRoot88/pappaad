from dataclasses import dataclass
from typing import Any, List, Dict, Optional
import re
import uuid
import logging
from google.ads.googleads.errors import GoogleAdsException
from google.api_core import protobuf_helpers
from google.ads.googleads.client import GoogleAdsClient
from app.ad.models import Ad, AdData
from .errors import GoogleAdsErrorHandler

logger = logging.getLogger(__name__)

# Constants
HEADLINE_MAX_LENGTH = 30
MIN_HEADLINES = 3
MIN_DESCRIPTIONS = 2
MAX_HEADLINES = 15
MAX_DESCRIPTIONS = 4


@dataclass
class AdGroupConfig:
    """Configuration for creating an ad group."""

    name: str
    type_: Any  # GoogleAds enum
    status: Any  # GoogleAds enum
    cpc_bid_micros: Optional[int] = None
    tracking_url_template: Optional[str] = None


@dataclass
class AdUpdateConfig:
    """Configuration for updating an ad."""

    headlines: Optional[List[Any]] = None
    descriptions: Optional[List[Any]] = None
    final_urls: Optional[List[str]] = None


class GoogleAdsTextAssetCreator:
    def __init__(self, client: GoogleAdsClient):
        self.client = client

    def create_text_asset(self, text: str, pinned_field: Optional[Any] = None) -> Any:
        """Create an AdTextAsset with optional pinning."""
        ad_text_asset = self.client.get_type("AdTextAsset")
        ad_text_asset.text = text
        if pinned_field:
            ad_text_asset.pinned_field = pinned_field
        return ad_text_asset

    def truncate_headlines(self, headlines: List[Any]) -> List[Any]:
        """Truncate headlines to maximum allowed length."""
        return [self.create_text_asset(headline.text[:HEADLINE_MAX_LENGTH]) for headline in headlines]


class GoogleAdsAdGroupManager:
    def __init__(self, client: GoogleAdsClient, googleads_account_id: str, googleads_campaign_id: Optional[str] = None):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.googleads_campaign_id = googleads_campaign_id
        self._ad_group_service = client.get_service("AdGroupService")
        self._campaign_service = client.get_service("CampaignService")

    def create_ad_group(self, config: AdGroupConfig) -> str:
        """
        Create an ad group with specified parameters.

        Args:
            config: AdGroupConfig containing the ad group settings

        Returns:
            str: The created ad group ID

        Raises:
            ValueError: If googleads_campaign_id is not set
        """
        self._validate_googleads_campaign_id()

        operation = self._create_ad_group_operation(config)
        response = self._execute_ad_group_operation(operation)

        return self._extract_ad_group_id(response)

    def _validate_googleads_campaign_id(self) -> None:
        """Ensure googleads_campaign_id is set before creating ad group."""
        if not self.googleads_campaign_id:
            raise ValueError("googleads_campaign_id is required for creating an ad group")

    def _create_ad_group_operation(self, config: AdGroupConfig) -> Any:
        """Create and configure the ad group operation."""
        operation = self.client.get_type("AdGroupOperation")
        ad_group = operation.create

        ad_group.name = config.name
        ad_group.status = config.status
        ad_group.type_ = config.type_
        ad_group.campaign = self._campaign_service.campaign_path(self.googleads_account_id, self.googleads_campaign_id)

        if config.cpc_bid_micros is not None:
            ad_group.cpc_bid_micros = config.cpc_bid_micros

        if config.tracking_url_template is not None:
            ad_group.tracking_url_template = config.tracking_url_template

        return operation

    def _execute_ad_group_operation(self, operation: Any) -> Any:
        """Execute the ad group creation operation."""
        return self._ad_group_service.mutate_ad_groups(customer_id=self.googleads_account_id, operations=[operation])

    def _extract_ad_group_id(self, response: Any) -> str:
        """Extract the ad group ID from the response."""
        return re.findall(r"adGroups\/(\d+)", response.results[0].resource_name)[0]

    def create_dynamic_ad_group(self) -> str:
        """Create a dynamic search ad group.

        Returns:
            str: The created ad group ID

        Raises:
            ValueError: If googleads_campaign_id is not set
        """
        config = AdGroupConfig(
            name=f"Dynamic Ad Group #{uuid.uuid4()}",
            type_=self.client.enums.AdGroupTypeEnum.SEARCH_DYNAMIC_ADS,
            status=self.client.enums.AdGroupStatusEnum.PAUSED,
            # Optionally add:
            # tracking_url_template="http://tracker.example.com/traveltracker/{escapedlpurl}"
            # cpc_bid_micros=10000000
        )

        return self.create_ad_group(config)


class AdValidator:
    """Handles validation logic for ads."""

    @staticmethod
    def validate_headlines_and_descriptions(headlines: List[Any], descriptions: List[Any]) -> None:
        """Validate minimum requirements for headlines and descriptions."""
        if len(headlines) < MIN_HEADLINES:
            raise ValueError(f"Number of Headlines must be {MIN_HEADLINES} or greater")
        if len(descriptions) < MIN_DESCRIPTIONS:
            raise ValueError(f"Number of Descriptions must be {MIN_DESCRIPTIONS} or greater")

    @staticmethod
    def validate_url(url: str) -> None:
        """Validate URL format."""
        if not url or not url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL format. Must start with http:// or https://")


class GoogleAdsAdIntegration:
    def __init__(self, client: GoogleAdsClient, googleads_account_id: str, googleads_campaign_id: Optional[str] = None):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.googleads_campaign_id = googleads_campaign_id
        self.errors = []
        self.asset_creator = GoogleAdsTextAssetCreator(client)
        self.group_manager = GoogleAdsAdGroupManager(client, googleads_account_id, googleads_campaign_id)
        self.validator = AdValidator()

    def create_responsive_search_ad(self, ad_group_id: str, ad: AdData) -> Optional[str]:
        """Create a responsive search ad with validation."""
        self._validate_ad_input(ad_group_id, ad)

        ad_group_ad = self._prepare_ad_group_ad(ad_group_id, ad)

        try:
            response = self.client.get_service("AdGroupAdService").mutate_ad_group_ads(
                customer_id=self.googleads_account_id, operations=[ad_group_ad]
            )
            return re.findall(r"adGroupAds\/(\d+~\d+)", response.results[0].resource_name)[0]
        except GoogleAdsException as ex:
            self.add_error(ex, ad)
            return None

    def _validate_ad_input(self, ad_group_id: str, ad: AdData) -> None:
        """Validate ad input parameters."""
        if not ad_group_id:
            raise ValueError("ad_group_id is required")
        self.validator.validate_url(ad.url)
        self.validator.validate_headlines_and_descriptions(ad.headlines, ad.descriptions)

    def _validate_update_input(self, ad: AdData) -> None:
        """Validate ad input parameters for updates."""
        self.validator.validate_headlines_and_descriptions(ad.headlines, ad.descriptions)

    def _prepare_ad_group_ad(self, ad_group_id: str, ad: AdData) -> Any:
        """Prepare ad group ad for creation."""
        googleads_ad_group_service = self.client.get_service("AdGroupService")

        # Create the ad group ad.
        googleads_ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
        googleads_ad_group_ad = googleads_ad_group_ad_operation.create
        googleads_ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
        googleads_ad_group_ad.ad_group = googleads_ad_group_service.ad_group_path(
            self.googleads_account_id, ad_group_id
        )
        # Set responsive search ad info.
        utm = "?utm_source=google&utm_medium=cpc&utm_campaign={{campaignid}}&utm_term={{keyword}}&utm_content={{creative}}"
        url = ad.url + utm
        googleads_ad_group_ad.ad.final_urls.append(url)
        # Set a pinning to always choose this asset for HEADLINE_1.

        # write a function that checks if all headlines are 30 characters or less
        # if not, truncate them

        if ad.headlines:
            googleads_ad_group_ad.ad.responsive_search_ad.headlines.extend(
                [self.asset_creator.create_text_asset(headline.text) for headline in ad.headlines[0:MAX_HEADLINES]]
            )
        if ad.descriptions:
            googleads_ad_group_ad.ad.responsive_search_ad.descriptions.extend(
                [
                    self.asset_creator.create_text_asset(description.text)
                    for description in ad.descriptions[0:MAX_DESCRIPTIONS]
                ]
            )

        return googleads_ad_group_ad_operation

    def update_responsive_search_ad(self, googleads_ad_id: str, ad: Ad) -> None:
        """Update a responsive search ad with new headlines and descriptions.

        Args:
            googleads_ad_id: The ID of the ad to update
            ad: Ad object containing new headlines and descriptions

        Raises:
            ValueError: If minimum headline or description requirements not met
            GoogleAdsException: If the update operation fails
        """
        if not googleads_ad_id:
            raise ValueError("googleads_ad_id is required")

        self._validate_update_input(ad)

        config = AdUpdateConfig(headlines=ad.headlines[:MAX_HEADLINES], descriptions=ad.descriptions[:MAX_DESCRIPTIONS])

        self._update_responsive_search_ad(googleads_ad_id, config)

    def _update_responsive_search_ad(self, googleads_ad_id: str, config: AdUpdateConfig) -> None:
        """Internal method to update a responsive search ad with given configuration.

        Args:
            googleads_ad_id: The ID of the ad to update
            config: AdUpdateConfig containing the fields to update

        Raises:
            GoogleAdsException: If the update operation fails
        """
        operation = self._prepare_update_operation(googleads_ad_id)
        googleads_ad = operation.update

        if config.headlines is not None:
            self._update_headlines(googleads_ad, config.headlines)

        if config.descriptions is not None:
            self._update_descriptions(googleads_ad, config.descriptions)

        if config.final_urls is not None:
            self._update_final_urls(googleads_ad, config.final_urls)

        self._execute_update_operation(operation, googleads_ad_id)

    def _prepare_update_operation(self, googleads_ad_id: str) -> Any:
        """Prepare the basic update operation structure."""
        ad_service = self.client.get_service("AdService")
        operation = self.client.get_type("AdOperation")
        operation.update.resource_name = ad_service.ad_path(self.googleads_account_id, googleads_ad_id)
        return operation

    def _update_headlines(self, googleads_ad: Any, headlines: List[Any]) -> None:
        """Update headlines for the ad."""
        googleads_ad.responsive_search_ad.headlines.clear()
        truncated_headlines = self.asset_creator.truncate_headlines(headlines)
        googleads_ad.responsive_search_ad.headlines.extend(truncated_headlines)

    def _update_descriptions(self, googleads_ad: Any, descriptions: List[Any]) -> None:
        """Update descriptions for the ad."""
        googleads_ad.responsive_search_ad.descriptions.clear()
        description_assets = [self.asset_creator.create_text_asset(desc.text) for desc in descriptions]
        googleads_ad.responsive_search_ad.descriptions.extend(description_assets)

    def _update_final_urls(self, googleads_ad: Any, urls: List[str]) -> None:
        """Update final URLs for the ad."""
        googleads_ad.final_urls.clear()
        googleads_ad.final_urls.extend(urls)

    def _execute_update_operation(self, operation: Any, googleads_ad_id: str) -> None:
        """Execute the update operation with error handling."""
        ad_service = self.client.get_service("AdService")

        # Set update mask
        self.client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask(None, operation.update._pb),
        )

        try:
            ad_service.mutate_ads(customer_id=self.googleads_account_id, operations=[operation])
        except GoogleAdsException as ex:
            # Use the existing error handler with the actual ad ID
            error = GoogleAdsErrorHandler.create_error(
                ex=ex, class_name="Ad", id=self.googleads_campaign_id, class_id=googleads_ad_id
            )
            self.errors.append(error)

    # Example of a new update method using the modular structure
    def update_ad_urls(self, googleads_ad_id: str, urls: List[str]) -> None:
        """Update only the URLs of an ad.

        Args:
            googleads_ad_id: The ID of the ad to update
            urls: List of new URLs to set

        Raises:
            GoogleAdsException: If the update operation fails
        """
        config = AdUpdateConfig(final_urls=urls)
        self._update_responsive_search_ad(googleads_ad_id, config)

    def create_googleads_ad_group(self, ad: AdData) -> str:
        """Create an ad group using ad data."""
        config = AdGroupConfig(
            name=f"Gl-{ad.url}-{uuid.uuid4()}",
            type_=self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD,
            status=self.client.enums.AdGroupStatusEnum.ENABLED,
            cpc_bid_micros=10000000,
        )
        return self.group_manager.create_ad_group(config)

    def add_dynamic_googleads_ad_group(self) -> str:
        """Create a dynamic search ad group.

        Returns:
            str: The ID of the created dynamic ad group

        Raises:
            ValueError: If googleads_campaign_id is not set
        """
        return self.group_manager.create_dynamic_ad_group()

    def add_error(self, ex: GoogleAdsException, ad: AdData) -> None:
        """Add a Google Ads error to the error list."""
        error = GoogleAdsErrorHandler.create_error(
            ex=ex,
            class_name="Ad",
            id=str(self.googleads_campaign_id),
            class_id=str(ad.id) if ad and hasattr(ad, "id") else None,
        )
        self.errors.append(error)

    def get_googleads_ads(self, googleads_ad_group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self.client
        googleads_account_id = self.googleads_account_id
        googleads_campaign_id = self.googleads_campaign_id
        googleads_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT ad_group.id, ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls
            FROM ad_group_ad
            WHERE ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
            AND ad_group_ad.status != "REMOVED"
            AND campaign.id = {googleads_campaign_id}
        """

        # Optional: Specify an ad group ID to restrict search to only a given
        # ad group.
        if googleads_ad_group_id:
            query += f" AND ad_group.id = {googleads_ad_group_id}"

        googleads_search_request = client.get_type("SearchGoogleAdsRequest")
        googleads_search_request.customer_id = googleads_account_id
        googleads_search_request.query = query
        results = googleads_service.search(request=googleads_search_request)

        one_found = False

        googleads_ads_ad_group = []
        for row in results:
            one_found = True
            googleads_ad = row.ad_group_ad.ad

            googleads_headlines = ad_text_assets_to_array(googleads_ad.responsive_search_ad.headlines)
            googleads_descriptions = ad_text_assets_to_array(googleads_ad.responsive_search_ad.descriptions)
            googleads_ads_ad_group.append(
                {
                    "ad_group_id": row.ad_group.id,
                    "ad_group_ad_name": row.ad_group_ad.ad.resource_name,
                    "ad_group_ad_id": row.ad_group_ad.ad.id,
                    "ad_group_ad_url": row.ad_group_ad.ad.final_urls,
                    "ad_group_ad_headlines": googleads_headlines,
                    "ad_group_ad_descriptions": googleads_descriptions,
                }
            )

        if not one_found:
            logger.info("No responsive search ads were found.")

        return googleads_ads_ad_group


def ad_text_assets_to_array(assets: List[Any]) -> List[str]:
    """Converts a list of AdTextAssets to a list of user-friendly strings."""
    s = []
    for asset in assets:
        s.append(asset.text)
    return s
