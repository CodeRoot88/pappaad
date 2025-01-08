import os

import stripe
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.ad.exception.handlers import register_ad_exception_handlers
from app.ad.router import router as ad_router
from app.auth.exception.handlers import authentication_exception_handlers
from app.auth.router import router as auth_router
from app.campaign.router import router as campaign_router
from app.google_ads.exception.handlers import register_google_ads_exception_handlers
from app.google_ads.router import router as google_ads_router
from app.headline.exception.handlers import register_headline_exception_handlers
from app.keyword.exception.handlers import register_keyword_exception_handlers
from app.task_tracking.router import router as task_tracking_router
from app.user.router import router as user_router
from app.organization.router import router as organization_router

load_dotenv()

# stripe.api_key = "sk_test_d15aTKAX5TPidn6P83U9d9dx" # use ur own stripe key
env = os.getenv("ENVIRONMENT", "dev")

if env in ["prod", "staging"]:
    import sentry_sdk

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", ""),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        environment=env,
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={*range(400, 599)},
                http_methods_to_capture=("GET",),
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={*range(400, 599)},
                http_methods_to_capture=("GET",),
            ),
        ],
    )


app = FastAPI()


origins = [
    "http://localhost:5173",
    "https://staging.glitchads.ai",
    "https://app.glitchads.ai",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_ad_exception_handlers(app)
register_google_ads_exception_handlers(app)
register_headline_exception_handlers(app)
register_keyword_exception_handlers(app)
authentication_exception_handlers(app)

app.include_router(auth_router)
app.include_router(campaign_router)
app.include_router(ad_router)
app.include_router(google_ads_router)
app.include_router(user_router)
app.include_router(task_tracking_router)
app.include_router(organization_router)


# we don't use this endpoint atm. It's for when we turn on billing
@app.post("/create-checkout-session")
def create_checkout_session():
    price_id = os.getenv("PRICE_ID", "")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        ui_mode="embedded",
        return_url="https://example.com/checkout/return?session_id={CHECKOUT_SESSION_ID}",
    )

    return session.client_secret
