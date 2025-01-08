from sqlmodel import Session

from app.common_schemas import UserProfile
from app.user.schemas import UserData

from app.user.db_ops import (
    add_user_account,
    get_all_users,
    get_user_account_by_email,
    get_user_account_by_id,
    update_user_account_refresh_token,
)
from app.user.models import UserAccountData
from app.auth.exception.exceptions import UserNotFoundException


def upsert_user_account(refresh_token: str, user_profile: UserProfile, db: Session) -> UserAccountData:
    if user_account := get_user_account_by_email(user_profile.email, db):
        user = get_user_account_by_id(user_account.id, db)
        if not user:
            raise UserNotFoundException("User Not Found.")
        user_account = update_user_account_refresh_token(user, refresh_token, db)
    else:
        user_account = add_user_account(refresh_token, user_profile, db)
    return user_account


def get_users(db: Session) -> list[UserData]:
    users = get_all_users(db)
    return [UserData(id=user.id, email=user.email, name=user.name, role=user.role) for user in users]
