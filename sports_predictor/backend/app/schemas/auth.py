from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Le mot de passe doit comporter au moins 6 caractères")
        return v

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Le nom d'utilisateur doit comporter au moins 3 caractères")
        if not v.isalnum():
            raise ValueError("Le nom d'utilisateur ne peut contenir que des lettres et chiffres")
        return v.lower()


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool


class LoginForm(BaseModel):
    username: str
    password: str
