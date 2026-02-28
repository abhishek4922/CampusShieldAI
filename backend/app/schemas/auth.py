"""
CampusShield AI — Auth Pydantic Schemas
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    role:          str


class ConsentRequest(BaseModel):
    consent_version: str = Field(default="1.0", description="Consent document version user agreed to")
    agreed:          bool = Field(..., description="Must be True to record consent")
