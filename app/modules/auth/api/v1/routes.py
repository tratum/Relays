from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)

from app.core.errors import ErrorResponse
from app.infra.guards.jwt import authenticate_jwt

from ...schemas.requests import (
    LoginUserRequestBody,
    RegisterUserRequestBody,
    RequestOTPRequestBody,
    VerifyRegistrationOTPRequestBody,
)
from ...schemas.response import (
    AuthenticateUserResponseBody,
    CurrentUserResponseBody,
    RequestOTPResponseBody,
    VerifyRegistrationOTPResponseBody,
)
from ...workflows.get_current_user import get_current_user
from ...workflows.login.authenticate_account import (
    authenticate_account,
)
from ...workflows.login.request_otp import request_login_otp
from ...workflows.registration.create_account import (
    create_account,
)
from ...workflows.registration.request_otp import (
    request_registration_otp,
)
from ...workflows.registration.verify_otp import (
    verify_registration_otp,
)

router = APIRouter(
    tags=["Authentication API"],
)


# -------------------------
# Health Check
# -------------------------


@router.get(
    "/auth/health",
    summary="Authentication Service Health Check",
    description=(
        "Returns the health status of the authentication module. "
        "This endpoint can be used by monitoring systems and "
        "load balancers to verify service availability."
    ),
)
async def health_check():
    return {"status": "ok"}


# ---------------------------------
# Registration: Request OTP
# ---------------------------------


@router.post(
    "/auth/register/request-otp",
    summary="Request Registration OTP",
    description=(
        "Generate and send a one-time password (OTP) to the supplied "
        "email address. The OTP must be verified before a new account "
        "can be created."
    ),
    response_model=RequestOTPResponseBody,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def request_registration_otp_route(
    req: RequestOTPRequestBody,
):
    await request_registration_otp(req.email)
    return RequestOTPResponseBody(
        message=(
            "If the email address is eligible for registration, "
            "a verification code has been sent."
        ),
    )


# ---------------------------------
# Registration: Verify OTP
# ---------------------------------


@router.post(
    "/auth/register/verify-otp",
    summary="Verify Registration OTP",
    description=(
        "Validate the OTP previously sent to the email address. "
        "Successful verification proves ownership of the email "
        "address and returns a short-lived registration token "
        "that can be used to complete account creation."
    ),
    response_model=VerifyRegistrationOTPResponseBody,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def verify_registration_otp_route(
    req: VerifyRegistrationOTPRequestBody,
):
    reg_token = await verify_registration_otp(
        email=req.email,
        otp=req.otp,
    )

    return VerifyRegistrationOTPResponseBody(registration_token=reg_token)


# ---------------------------------
# Registration: Complete Account Creation
# ---------------------------------


@router.post(
    "/auth/register",
    summary="Complete Account Registration",
    description=(
        "Create a new Relays account using a previously issued "
        "registration token. This operation creates the user, "
        "workspace, and workspace membership atomically and "
        "returns a JWT access token."
    ),
    response_model=AuthenticateUserResponseBody,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_account_route(
    req: RegisterUserRequestBody,
):
    access_token = await create_account(
        registration_token=req.registration_token,
        name=req.name,
        workspace_name=req.workspace_name,
    )

    return AuthenticateUserResponseBody(
        access_token=access_token,
        token_type="Bearer",
    )


# ---------------------------------
# Login: Request OTP
# ---------------------------------


@router.post(
    "/auth/login/request-otp",
    summary="Request Login OTP",
    description=(
        "Generate and send a one-time password (OTP) to the supplied "
        "email address. If an account exists for the email address, "
        "a login code will be generated and delivered."
    ),
    response_model=RequestOTPResponseBody,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def request_login_otp_route(
    req: RequestOTPRequestBody,
):
    await request_login_otp(req.email)

    return RequestOTPResponseBody(
        message=(
            "If an account exists for this email address, "
            "a login code has been sent."
        ),
    )


# ---------------------------------
# Login
# ---------------------------------


@router.post(
    "/auth/login",
    summary="Authenticate User",
    description=(
        "Validate the supplied email address and login OTP. "
        "Upon successful verification a JWT access token is "
        "issued for authenticated access to protected APIs."
    ),
    response_model=AuthenticateUserResponseBody,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def login_route(
    req: LoginUserRequestBody,
):
    access_token = await authenticate_account(
        email=req.email,
        otp=req.otp,
    )

    return AuthenticateUserResponseBody(
        access_token=access_token,
        token_type="Bearer",
    )


# ---------------------------------
# Current User
# ---------------------------------


@router.get(
    "/auth/me",
    summary="Get Current Authenticated User",
    description=(
        "Return information about the currently authenticated "
        "user and their workspace using the JWT access token "
        "provided in the Authorization header."
    ),
    response_model=CurrentUserResponseBody,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    dependencies=[Depends(authenticate_jwt)],
)
async def current_user_route(
    req: Request,
):
    result = await get_current_user(
        user_id=req.state.user_id,
    )

    return CurrentUserResponseBody(**result)
