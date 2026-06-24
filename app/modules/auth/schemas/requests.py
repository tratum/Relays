from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .validators import (
    EmailAddress,
    OTPCode,
    RefreshToken,
    UserName,
    WorkspaceName,
)


class RequestOTPRequestBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    email: EmailAddress = Field(
        ...,
        description=(
            "Email address associated with the account or registration request."
        ),
        examples=["owner@acme.com"],
    )


class VerifyRegistrationOTPRequestBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    email: EmailAddress = Field(
        ...,
        description=("Email address that is being verified."),
        examples=["owner@acme.com"],
    )

    otp: OTPCode = Field(
        ...,
        description=("Verification code sent to the email address."),
        examples=["123456"],
    )


class RegisterUserRequestBody(
    BaseModel,
):
    model_config = ConfigDict(
        extra="forbid",
    )

    registration_token: str = Field(
        ...,
        description=(
            "Short-lived token issued after successful email verification."
        ),
    )

    name: UserName = Field(
        ...,
        description=("Full name of the user."),
        examples=["John Doe"],
    )

    workspace_name: WorkspaceName = Field(
        ...,
        description=(
            "Human-readable name of the workspace. "
            "This name is used to generate the workspace slug."
        ),
        examples=[
            "Acme",
            "Acme Corporation",
            "Relays Production",
        ],
    )


class LoginUserRequestBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    email: EmailAddress = Field(
        ...,
        description=("Email address associated with the account."),
        examples=["owner@acme.com"],
    )

    otp: OTPCode = Field(
        ...,
        description=("One-time password sent to the user's email address."),
        examples=["123456"],
    )


class RefreshAccessTokenRequestBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    refresh_token: RefreshToken = Field(
        ...,
        description=("Refresh token issued during authentication."),
        examples=["Vw0hBvLq3fAq5XJm1q4sX6wKc8rPnYz..."],
    )


class LogoutRequestBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    refresh_token: RefreshToken = Field(
        ...,
        description=("Refresh token identifying the session to revoke."),
        examples=["Vw0hBvLq3fAq5XJm1q4sX6wKc8rPnYz..."],
    )
