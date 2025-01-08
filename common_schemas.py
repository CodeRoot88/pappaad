from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    name: str
    email: EmailStr
    picture: str
