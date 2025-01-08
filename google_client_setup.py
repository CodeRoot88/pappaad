import os
from google.ads.googleads.client import GoogleAdsClient
from dotenv import load_dotenv

load_dotenv()


def initialize_googleads_client(refresh_token: str, googleads_manager_id=None) -> GoogleAdsClient:
    credentials = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }
    if googleads_manager_id:
        if googleads_manager_id == "{}":
            credentials["login_customer_id"] = None
        else:
            credentials["login_customer_id"] = googleads_manager_id
    return GoogleAdsClient.load_from_dict(credentials)  # type: ignore


def initialize_googleads_client_without_login_customer_id(refresh_token: str) -> GoogleAdsClient:
    credentials = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }

    return GoogleAdsClient.load_from_dict(credentials)  # type: ignore
