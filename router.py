from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.endpoint_dependencies import check_admin_user

from app.database import get_db_session
from app.user.models import UserAccount
from app.user.services import get_users as get_db_users
from app.auth.services.impersonate import set_impersonate_user, unset_impersonate_user

router = APIRouter()


@router.get("/users")
def get_users(
    admin_user=Depends(check_admin_user),
    db: Session = Depends(get_db_session),
):
    return get_db_users(db)


@router.post("/user/{email}/impersonate")
def set_impersonated_user(
    email: str,
    admin_user: UserAccount = Depends(check_admin_user),
    db: Session = Depends(get_db_session),
):
    return set_impersonate_user(admin=admin_user, target_user_email=email, db=db)


@router.post("/user/unset_impersonate")
def unset_impersonated_user(
    admin_user=Depends(check_admin_user),
    db: Session = Depends(get_db_session),
):
    return unset_impersonate_user(admin=admin_user, db=db)
