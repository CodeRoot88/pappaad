from google.ads.googleads.client import GoogleAdsClient


class GoogleAdsAccountLinkIntegration:
    def __init__(self, client: GoogleAdsClient, googleads_account_id: str, manager_account_id: str | None):
        self.client = client
        self.googleads_account_id = googleads_account_id
        self.manager_account_id = manager_account_id

    def link_account_to_manager(self):
        # Initialize the Google Ads API client
        client = self.client
        googleads_account_id = self.googleads_account_id
        manager_account_id = self.manager_account_id

        # Get the CustomerClientLinkService client
        customer_client_link_service = client.get_service("CustomerClientLinkService")

        # Create a new operation for linking the client account to the manager account
        client_link_operation = client.get_type("CustomerClientLinkOperation")
        client_link = client_link_operation.create
        client_link.client_customer = f"customers/{googleads_account_id}"
        client_link.status = client.enums.ManagerLinkStatusEnum.PENDING

        # Execute the operation to create the link
        customer_client_link_service.mutate_customer_client_link(
            customer_id=manager_account_id, operation=client_link_operation
        )
        return True
