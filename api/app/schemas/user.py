import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationRead(BaseModel):
    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Registers a brand-new organization with this user as its owner."""

    email: EmailStr
    password: str = Field(min_length=8)
    org_name: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    organization: OrganizationRead

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InviteCreate(BaseModel):
    email: EmailStr


class InviteRead(BaseModel):
    invite_token: str
    expires_at: int
    """Unix timestamp (seconds) the invite token expires at."""


class InviteAccept(BaseModel):
    invite_token: str
    password: str = Field(min_length=8)
