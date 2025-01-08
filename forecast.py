from google.ads.googleads.client import GoogleAdsClient

from typing import Any
from datetime import datetime, timedelta
import json


def forecast_campaign(
    client: GoogleAdsClient,
    googleads_account_id: str,
    country_code: str,
    location_query: str,
    ad_groups: list[Any],
    locations: list[Any] | None = None,
):
    campaign_to_forecast = create_campaign_to_forecast(
        client=client, ads=ad_groups, location_query=location_query, country_code=country_code, locations=locations
    )
    if not campaign_to_forecast:
        return False
    return generate_forecast_metrics(
        client=client, googleads_account_id=googleads_account_id, campaign_to_forecast=campaign_to_forecast[0]
    )


def forecast_campaign_with_locations(
    client: GoogleAdsClient,
    googleads_account_id: str,
    country_code: str,
    location_query: str,
    ad_groups: list[Any],
    locations: list[Any] | None = None,
):
    campaign_to_forecast = create_campaign_to_forecast(
        client=client, ads=ad_groups, location_query=location_query, country_code=country_code, locations=locations
    )
    if not False:
        return False
    return [
        generate_forecast_metrics(
            client=client,
            googleads_account_id=googleads_account_id,
            campaign_to_forecast=campaign_to_forecast[0],
        ),
        campaign_to_forecast[1],
    ]


def create_campaign_to_forecast(
    client: GoogleAdsClient, ads: list[Any], location_query: str, country_code: str, locations: list[Any] | None = None
):
    """Creates the campaign to forecast.

    A campaign to forecast lets you try out various configurations and keywords
    to find the best optimization for your future campaigns. Once you've found
    the best campaign configuration, create a serving campaign in your Google
    Ads account with similar values and keywords. For more details, see:
    https://support.google.com/google-ads/answer/3022575

    Args:
        client: an initialized GoogleAdsClient instance.

    Returns:
        An CampaignToForecast instance.
    """
    return_location = None
    googleads_service = client.get_service("GoogleAdsService")
    gtc_service = client.get_service("GeoTargetConstantService")
    # Retrieve the geo target constant for Hamburg
    # Note: Replace 'Hamburg' with the specific city name in Hamburg if needed
    gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")
    gtc_request.locale = "en"
    gtc_request.country_code = country_code
    if not locations:
        # The location names to get suggested geo target constants.
        if not location_query:
            return False
        gtc_request.location_names.names.extend([location_query])
        results = gtc_service.suggest_geo_target_constants(gtc_request)
        if not results.geo_target_constant_suggestions:
            return False
        geo_target_constant = results.geo_target_constant_suggestions[0].geo_target_constant.id
        return_location = results.geo_target_constant_suggestions[0].geo_target_constant

    # Create a campaign to forecast.
    campaign_to_forecast = client.get_type("CampaignToForecast")
    campaign_to_forecast.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    # Set the bidding strategy.
    campaign_to_forecast.bidding_strategy.manual_cpc_bidding_strategy.max_cpc_bid_micros = 1000000

    # For the list of geo target IDs, see:
    # https://developers.google.com/google-ads/api/reference/data/geotargets
    criterion_bid_modifier = client.get_type("CriterionBidModifier")
    # Geo target constant 2840 is for USA.
    if locations:
        for location in locations:
            location = location[0]
            criterion_bid_modifier.geo_target_constant = googleads_service.geo_target_constant_path(location)
            campaign_to_forecast.geo_modifiers.append(criterion_bid_modifier)
    else:
        criterion_bid_modifier.geo_target_constant = googleads_service.geo_target_constant_path(geo_target_constant)
        campaign_to_forecast.geo_modifiers.append(criterion_bid_modifier)
    # For the list of language criteria IDs, see:
    # https://developers.google.com/google-ads/api/reference/data/codes-formats#languages
    # Language criteria 1000 is for English.
    campaign_to_forecast.language_constants.append(googleads_service.language_constant_path("1000"))

    # Create forecast ad groups based on themes such as creative relevance,
    # product category, or cost per click.
    for ad in ads:
        keywords = ad.keywords

        forecast_ad_group = client.get_type("ForecastAdGroup")

        biddable_keywords = []

        if isinstance(keywords, str):
            keywords = json.loads(keywords).get("keywords")

        if not keywords:
            continue
        for keyword in keywords:
            biddable_keyword = client.get_type("BiddableKeyword")
            biddable_keyword.max_cpc_bid_micros = 2500000
            biddable_keyword.keyword.text = keyword.text
            biddable_keyword.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
            biddable_keywords.append(biddable_keyword)

        # Add the biddable keywords to the forecast ad group.
        forecast_ad_group.biddable_keywords.extend(biddable_keywords)

        campaign_to_forecast.ad_groups.append(forecast_ad_group)

    return [campaign_to_forecast, return_location]


def generate_forecast_metrics(client: GoogleAdsClient, googleads_account_id: str, campaign_to_forecast):
    """Generates forecast metrics and prints the results.

    Args:
        client: an initialized GoogleAdsClient instance.
        customer_id: a client customer ID.
        campaign_to_forecast: a CampaignToForecast to generate metrics for.
    """
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordForecastMetricsRequest")
    request.customer_id = googleads_account_id
    request.campaign = campaign_to_forecast

    # Set the forecast range. Repeat forecasts with different horizons to get a
    # holistic picture.
    # Set the forecast start date to tomorrow.
    tomorrow = datetime.now() + timedelta(days=1)
    request.forecast_period.start_date = tomorrow.strftime("%Y-%m-%d")
    # Set the forecast end date to 30 days from today.
    thirty_days_from_now = datetime.now() + timedelta(days=30)
    request.forecast_period.end_date = thirty_days_from_now.strftime("%Y-%m-%d")
    response = keyword_plan_idea_service.generate_keyword_forecast_metrics(request=request)

    return response.campaign_forecast_metrics
