from google.ads.googleads.client import GoogleAdsClient

import os


class GoogleAdsClientIntegration:
    def __init__(
        self,
        refresh_token: str,
        googleads_account_id: str | None = None,
        manager_account_id: str | None = None,
    ):
        self.googleads_account_id = googleads_account_id
        self.refresh_token = refresh_token
        self.client = self.get_client_from_refresh_token(refresh_token, manager_account_id=manager_account_id)

    def get_client_from_refresh_token(self, refresh_token: str, manager_account_id: str | None = None):
        if manager_account_id:
            config = {
                "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                "use_proto_plus": True,
                "login_customer_id": manager_account_id,
            }
        else:
            config = {
                "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                "use_proto_plus": True,
            }

        return GoogleAdsClient.load_from_dict(config)

    def stub(self):
        return self.get_client_from_refresh_token(
            "1//09ovx9tiCLGrnCgYIARAAGAkSNwF-L9Irn3bYbrLTA6c6V1l1XIVAAKjGf_8AGNBhq2TWOkkX-SZIiXqHgiIjZxMRfwigPwk4PKg"
        )
