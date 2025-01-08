from enum import Enum

from app.membership.schemas import MembershipData
from pydantic import BaseModel, ConfigDict


class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserData(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole | None = None

    model_config = ConfigDict(use_enum_values=True)


class UserAccountWithMembership(BaseModel):
    name: str
    email: str
    role: UserRole
    membership: MembershipData
