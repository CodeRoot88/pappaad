from google.ads.googleads.errors import GoogleAdsException


class GoogleAdsLocationIntegration:
    def __init__(self, client=None, googleads_account_id=None, googleads_campaign_id=None):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.googleads_campaign_id = googleads_campaign_id

    def get_locations_for_googleads_campaign(self):
        query = f"""
            SELECT campaign_criterion.location.geo_target_constant 
            FROM campaign_criterion 
            WHERE campaign_criterion.type = 'LOCATION' 
            AND campaign.id = {self.googleads_campaign_id}
            """
        googleads_service = self.client.get_service("GoogleAdsService")
        results = googleads_service.search_stream(query=query, customer_id=self.googleads_account_id)

        googleads_locations = []
        for batch in results:
            for row in batch.results:
                googleads_locations.append(row.campaign_criterion)
        return googleads_locations


def get_geo_target_suggestions_by_search_string(client, search_string):
    """
    Function to get geo target suggestions based on a search string (e.g., location name).

    Args:
        client: An instantiated Google Ads API client.
        search_string: The location name for which geo target suggestions are required.

    Returns:
        List of geo target suggestions.
    """
    # Create an instance of the GeoTargetConstantService
    try:
        gtc_service = client.get_service("GeoTargetConstantService")

        gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")

        gtc_request.locale = "en"
        # not a real commit

        # The location names to get suggested geo target constants.
        gtc_request.location_names.names.extend([search_string])

        results = gtc_service.suggest_geo_target_constants(gtc_request)
        suggestions = []
        for suggestion in results.geo_target_constant_suggestions:
            geo_target_constant = suggestion.geo_target_constant
            suggestions.append(
                {
                    "criteria_id": geo_target_constant.id,
                    "name": geo_target_constant.name,
                    "canonical_name": geo_target_constant.canonical_name,
                    "country_code": geo_target_constant.country_code,
                    "target_type": geo_target_constant.target_type,
                    "status": "Active" if geo_target_constant.status.name == "ENABLED" else "Removal Planned",
                    "locale": suggestion.locale,
                    "reach": suggestion.reach,
                    "search_term": suggestion.search_term,
                }
            )

        return suggestions

    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name}: {ex.error.message}")
        raise


def get_geo_nearby_suggestions_by_get_targets(client, criterion_id: int):
    """
    Function to get geo target suggestions based on a search string (e.g., location name).

    Args:
        client: An instantiated Google Ads API client.
        search_string: The location name for which geo target suggestions are required.

    Returns:
        List of geo target suggestions.
    """
    # Create an instance of the GeoTargetConstantService
    try:
        gtc_service = client.get_service("GeoTargetConstantService")

        gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")

        gtc_request.locale = "en"

        resource_name = gtc_service.geo_target_constant_path(criterion_id)
        gtc_request.geo_targets.geo_target_constants.append(resource_name)

        results = gtc_service.suggest_geo_target_constants(gtc_request)
        suggestions = []
        for suggestion in results.geo_target_constant_suggestions:
            geo_target_constant = suggestion.geo_target_constant

            suggestions.append(
                {
                    "criteria_id": geo_target_constant.id,
                    "name": geo_target_constant.name,
                    "canonical_name": geo_target_constant.canonical_name,
                    "country_code": geo_target_constant.country_code,
                    "target_type": geo_target_constant.target_type,
                    "status": "Active" if geo_target_constant.status.name == "ENABLED" else "Removal Planned",
                    "locale": suggestion.locale,
                    "reach": suggestion.reach,
                    "search_term": suggestion.search_term,
                }
            )

        return suggestions

    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name}: {ex.error.message}")
        raise
