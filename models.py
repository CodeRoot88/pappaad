from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.user.schemas import UserRole

from app.membership.models import Membership
from app.organization.models import Organization

if TYPE_CHECKING:
    from app.campaign.models import Campaign
    from app.google_ads.models import GoogleAdsAccount


class UserAccountBase(SQLModel):
    name: str
    picture: Optional[str] | None = Field(default=None)
    email: str = Field(unique=True)
    password: Optional[str] | None = Field(default=None)
    google_refresh_token: Optional[str] | None = Field(default=None)
    role: UserRole = Field(default=UserRole.USER)


class UserAccount(UserAccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    organizations: list["Organization"] = Relationship(back_populates="users", link_model=Membership)
    campaigns: list["Campaign"] = Relationship(back_populates="user_account")
    googleads_accounts: list["GoogleAdsAccount"] = Relationship(back_populates="user_account")


class UserAccountData(UserAccountBase):
    id: int
