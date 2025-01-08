from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from app.campaign.asset_models import Callout, PhoneNumber, PriceRead, SiteLinkData, StructuredSnippetData
from .assets.sitelink import GoogleAdsSiteLinkIntegration
from .assets.callout import GoogleAdsCalloutIntegration
from .assets.structured_snippet import GoogleAdsStructuredSnippetIntegration
from .assets.call import GoogleAdsCallIntegration
from .assets.price import GoogleAdsPriceIntegration
from .errors import GoogleAdsErrorHandler


class GoogleAdsAssetIntegration:
    def __init__(
        self,
        client: GoogleAdsClient,
        googleads_account_id: str,
        campaign_id: int,
        googleads_campaign_id: str | None = None,
    ):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.googleads_campaign_id = googleads_campaign_id
        self.campaign_id = campaign_id
        self.errors = []

        # Initialize integrations
        self.sitelink_integration = GoogleAdsSiteLinkIntegration(
            client, googleads_account_id, campaign_id, googleads_campaign_id
        )
        self.callout_integration = GoogleAdsCalloutIntegration(
            client, googleads_account_id, campaign_id, googleads_campaign_id
        )
        self.structured_snippet_integration = GoogleAdsStructuredSnippetIntegration(
            client, googleads_account_id, campaign_id, googleads_campaign_id
        )
        self.call_integration = GoogleAdsCallIntegration(
            client, googleads_account_id, campaign_id, googleads_campaign_id
        )
        self.price_integration = GoogleAdsPriceIntegration(
            client, googleads_account_id, campaign_id, googleads_campaign_id
        )

    def add_error(self, ex: GoogleAdsException, class_name: str = "Asset") -> None:
        """Add a Google Ads error to the error list."""
        error = GoogleAdsErrorHandler.create_error(
            ex=ex, class_name=class_name, id=str(self.campaign_id), class_id=str(self.campaign_id)
        )
        self.errors.append(error)

    def create_googleads_site_links_assets(self, site_links: list["SiteLinkData"]):
        return self.sitelink_integration.create_googleads_assets(site_links)

    def create_googleads_callouts_assets(self, callouts: list["Callout"]):
        return self.callout_integration.create_googleads_assets(callouts)

    def create_googleads_structured_snippet(self, structured_snippets: list["StructuredSnippetData"]):
        return self.structured_snippet_integration.create_googleads_assets(structured_snippets)

    def create_googleads_price_assets(self, prices: list["PriceRead"]):
        return self.price_integration.create_googleads_assets(prices)

    def create_google_ads_call_asset(
        self, glitch_phone_number, conversion_action_id=None, resource="Account", resource_id=None
    ):
        return self.call_integration.create_google_ads_call_asset(
            glitch_phone_number, conversion_action_id, resource, resource_id
        )

    def attach_call_to_campaign(self, phone_number_resource_name):
        return self.call_integration.attach_call_to_campaign(phone_number_resource_name)

    def update_googleads_site_link_assets(self, site_links: list["SiteLinkData"]):
        return self.sitelink_integration.update_googleads_assets(site_links)

    def update_googleads_callout_assets(self, callouts: list["Callout"]):
        return self.callout_integration.update_googleads_assets(callouts)

    def update_googleads_structured_snippet(self, structured_snippets: list["StructuredSnippetData"]):
        return self.structured_snippet_integration.update_googleads_assets(structured_snippets)

    def update_googleads_price_assets(self, prices: list["PriceRead"]):
        return self.price_integration.update_googleads_assets(prices)

    def update_googleads_call_asset(self, phone_numbers: list["PhoneNumber"]):
        return self.call_integration.update_googleads_call_asset(phone_numbers)

    def get_googleads_calls_for_campaign(self):
        return self.call_integration.get_googleads_calls_for_campaign()

    def get_googleads_callouts_for_campaign(self):
        return self.callout_integration.get_googleads_callouts_for_campaign()

    def get_googleads_sitelinks_for_campaign(self):
        return self.sitelink_integration.get_googleads_sitelinks_for_campaign()

    def get_googleads_structured_snippets_for_campaign(self):
        return self.structured_snippet_integration.get_googleads_structured_snippets_for_campaign()

    def get_googleads_prices_for_campaign(self):
        return self.price_integration.get_googleads_prices_for_campaign()
