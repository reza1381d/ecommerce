from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    ResourceNotFoundError,
)


def handle_resource_not_found(
    request: Request,
    exc: ResourceNotFoundError,
) -> JSONResponse:

    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
        },
    )


def handle_conflict(
    request: Request,
    exc: ConflictError,
) -> JSONResponse:

    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
        },
    )


def handle_business_rule(
    request: Request,
    exc: BusinessRuleError,
) -> JSONResponse:

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )


def handle_authentication(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:

    return JSONResponse(
        status_code=401,
        content={
            "detail": str(exc),
        },
    )


def handle_domain_error(
    request: Request,
    exc: DomainError,
) -> JSONResponse:

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )