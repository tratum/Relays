from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
)

from .validators import (
    EmailAddress,
    RefreshToken,
    UserName,
    WorkspaceName,
)


class RequestOTPResponseBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    message: str = Field(
        ...,
        description=(
            "Human-readable confirmation that the OTP request was accepted."
        ),
        examples=[
            "If an account exists for this email address, a verification code has been sent."
        ],
    )


class VerifyRegistrationOTPResponseBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    registration_token: str = Field(
        ...,
        description=(
            "Short-lived token proving ownership of the verified email address."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class AuthenticateUserResponseBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    access_token: str = Field(
        ...,
        description=(
            "JWT access token issued after successful authentication."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )

    refresh_token: RefreshToken = Field(
        ...,
        description=(
            "Long-lived refresh token used to obtain new access tokens "
            "without requiring the user to authenticate again."
        ),
        examples=["k2v4Y7nJQ8fT..."],
    )

    token_type: str = Field(
        ...,
        description=("Authentication scheme used in the Authorization header."),
        examples=["Bearer"],
    )


class CurrentUserResponseBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    user_id: UUID4 = Field(
        ...,
        description=("Unique identifier of the authenticated user."),
        examples=["d290f1ee-6c54-4b01-90e6-d701748f0851"],
    )

    workspace_id: UUID4 = Field(
        ...,
        description=("Unique identifier of the user's workspace."),
        examples=["8d67a6e7-f2ef-4eb9-9d26-5ef1f3b2d911"],
    )

    name: UserName = Field(
        ...,
        description=("Display name of the authenticated user."),
        examples=["John Doe"],
    )

    email: EmailAddress = Field(
        ...,
        description=("Email address of the authenticated user."),
        examples=["owner@acme.com"],
    )

    workspace_name: WorkspaceName = Field(
        ...,
        description=("Display name of the user's workspace."),
        examples=["Acme Corporation"],
    )


class LogoutResponseBody(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
    )

    message: str = Field(
        ...,
        description=(
            "Human-readable confirmation that the session was revoked."
        ),
        examples=["Logged out successfully."],
    )
