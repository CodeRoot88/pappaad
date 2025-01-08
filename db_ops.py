from typing import Optional

from sqlmodel import Session, select

from app.user.schemas import UserRole

from app.common_schemas import UserProfile
from .models import UserAccount, UserAccountData


def get_user_account_data_by_email(email: str, db: Session) -> UserAccountData | None:
    statement = select(UserAccount).where(UserAccount.email == email)
    user = db.exec(statement).first()
    if user:
        return UserAccountData.model_validate(user)
    return None


def get_user_account_by_email(email: str, db: Session) -> UserAccountData | None:
    statement = select(UserAccount).where(UserAccount.email == email)
    user = db.exec(statement).first()
    if user:
        return UserAccountData.model_validate(user)
    return None


def fetch_user_account_by_email(email: str, db: Session) -> UserAccount | None:
    statement = select(UserAccount).where(UserAccount.email == email)
    return db.exec(statement).first()


def update_user_account_refresh_token(user: UserAccount, refresh_token: str, db: Session) -> UserAccountData:
    user.google_refresh_token = refresh_token
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserAccountData.model_validate(user)


def add_user_account(refresh_token: str, user_profile: UserProfile, db: Session) -> UserAccountData:
    account = UserAccount(google_refresh_token=refresh_token, **user_profile.model_dump())
    account.role = UserRole.USER
    account.password = ""
    db.add(account)
    db.commit()
    db.refresh(account)
    return UserAccountData.model_validate(account)


def get_user_account_by_id(user_account_id: int, db: Session) -> Optional[UserAccount]:
    statement = select(UserAccount).where(UserAccount.id == user_account_id)
    user_account = db.exec(statement).first()
    return user_account


def get_all_users(db: Session):
    statement = select(UserAccount)
    return db.exec(statement).all()


def add_user(user: UserAccount, db: Session) -> UserAccountData:
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserAccountData.model_validate(user)
