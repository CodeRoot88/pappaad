import os
from typing import TYPE_CHECKING

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.campaign.models import CampaignData
from app.organization.services.organization import get_organization_by_slug_or_id
from app.membership.db_ops import get_membership

from app.campaign.db_ops import get_user_campaign_by_id, get_user_campaign_by_slug
from app.database import get_db_session
from app.google_ads.db_ops import get_current_user_selected_google_ads_customer
from app.user.db_ops import get_user_account_by_email, get_user_account_data_by_email
from app.user.schemas import UserRole
from app.organization.models import OrganizationData
from app.membership.schemas import MembershipRole
from app.membership.models import Membership

if TYPE_CHECKING:
    from .google_ads.models import GoogleAdsAccountData
    from .user.models import UserAccountData

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
security = HTTPBearer()

credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        if not email:
            raise credentials_exception
        return payload

    except jwt.PyJWTError:
        raise credentials_exception


def is_admin(email: str, db: Session) -> bool:
    user = get_user_account_by_email(email, db)
    if not user or not user.id:
        raise HTTPException(status_code=404, detail="User not found")
    return user.role == UserRole.ADMIN


def check_admin_user(
    payload: dict = Depends(verify_jwt_token), db: Session = Depends(get_db_session)
) -> "UserAccountData":
    email = str(payload.get("email"))

    if not is_admin(email, db):
        raise credentials_exception
    admin_user = get_user_account_by_email(email, db)
    if not admin_user:
        raise HTTPException(status_code=404, detail="User not found")
    return admin_user


def check_impersonate(
    payload: dict = Depends(verify_jwt_token),
    db: Session = Depends(get_db_session),
) -> str:
    email = str(payload.get("email"))
    impersonating_email = payload.get("impersonating_email")
    if not impersonating_email:
        return email

    if is_admin(email, db):
        return str(impersonating_email)
    else:
        raise HTTPException(status_code=403, detail="Permission denied")


def get_current_user(
    email: str = Depends(check_impersonate), db: Session = Depends(get_db_session)
) -> "UserAccountData":
    user = get_user_account_data_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_googleads_account(
    current_user: "UserAccountData" = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> "GoogleAdsAccountData":
    current_selected_google_customer = get_current_user_selected_google_ads_customer(current_user.id, db)
    if not current_selected_google_customer:
        raise HTTPException(status_code=404, detail="No Google Ads account selected")

    return current_selected_google_customer


def get_user_campaign_by_slug_or_id(
    user_id: int, db: Session, slug: str | None = None, id: int | None = None
) -> "CampaignData":
    campaign = None
    if slug:
        campaign = get_user_campaign_by_slug(slug, user_id, db)
    if not campaign and id:
        campaign = get_user_campaign_by_id(id, user_id, db)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def get_user_campaign(
    db: Session = Depends(get_db_session),
    current_user: "UserAccountData" = Depends(get_current_user),
    campaign_slug: str | None = None,
    campaign_id: int | None = None,
) -> "CampaignData":
    return get_user_campaign_by_slug_or_id(user_id=current_user.id, db=db, slug=campaign_slug, id=campaign_id)


def get_glitch_refresh_token(db: Session = Depends(get_db_session)):
    glitch_email = os.environ.get("GLITCH_USER_EMAIL")
    if not glitch_email:
        raise HTTPException(status_code=404, detail="GLITCH_USER_EMAIL not found")
    glitch_user = get_user_account_by_email(glitch_email, db)
    if not glitch_user:
        raise HTTPException(status_code=404, detail="Glitch user not found")
    return glitch_user.google_refresh_token


# organization endpoint dependency
def check_organization_owner(
    organization: "OrganizationData" = Depends(get_organization_by_slug_or_id),
    current_user: "UserAccountData" = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Membership:
    membership = get_membership(organization_id=organization.id, user_id=current_user.id, db=db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access to this organization is not permitted.")
    elif membership.role != MembershipRole.OWNER:
        raise HTTPException(status_code=403, detail="Access denied. You are not the owner of this organization.")
    return membership


def check_organization_member(
    organization: "OrganizationData" = Depends(get_organization_by_slug_or_id),
    current_user: "UserAccountData" = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Membership:
    membership = get_membership(organization_id=organization.id, user_id=current_user.id, db=db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access to this organization is not permitted.")
    return membership
