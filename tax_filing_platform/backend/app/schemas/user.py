from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: UserRole
    wallet_address: str | None = None


class WalletLink(BaseModel):
    wallet_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
