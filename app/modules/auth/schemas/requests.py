from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .validators import (
    EmailAddress,
    OTPCode,
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
        frozen=True,
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
        description=("Display name of the workspace."),
        examples=["Acme Corporation"],
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
