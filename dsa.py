def create_dynamic_search_ad(googleads_client, googleads_account_id, googleads_campaign_id, description, campaign_name):
    campaign_service = googleads_client.get_service("CampaignService")
    googleads_ad_group_service = googleads_client.get_service("AdGroupService")
    googleads_ad_group_ad_service = googleads_client.get_service("AdGroupAdService")

    # Update the campaign to enable dynamic search ads

    # Create a new ad group for dynamic search ads
    googleads_ad_group_operation = googleads_client.get_type("AdGroupOperation")
    googleads_ad_group = googleads_ad_group_operation.create
    googleads_ad_group.name = f"Dynamic Search Ad Group for {campaign_name}"
    googleads_ad_group.campaign = campaign_service.campaign_path(googleads_account_id, googleads_campaign_id)
    googleads_ad_group.type_ = googleads_client.enums.AdGroupTypeEnum.SEARCH_DYNAMIC_ADS
    googleads_ad_group.status = googleads_client.enums.AdGroupStatusEnum.ENABLED

    # Submit ad group creation request
    googleads_ad_group_response = googleads_ad_group_service.mutate_ad_groups(
        customer_id=googleads_account_id, operations=[googleads_ad_group_operation]
    )
    googleads_ad_group_resource_name = googleads_ad_group_response.results[0].resource_name
    print(f"Created ad group with resource name: {googleads_ad_group_resource_name}")

    # Create a dynamic search ad in the ad group
    googleads_ad_group_ad_operation = googleads_client.get_type("AdGroupAdOperation")
    googleads_ad_group_ad = googleads_ad_group_ad_operation.create
    googleads_ad_group_ad.ad_group = googleads_ad_group_resource_name
    googleads_ad_group_ad.ad.expanded_dynamic_search_ad.description = description
    googleads_ad_group_ad.status = "ENABLED"

    # Submit ad group ad creation request
    googleads_ad_group_ad_service.mutate_ad_group_ads(
        customer_id=googleads_account_id, operations=[googleads_ad_group_ad_operation]
    )
