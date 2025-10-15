"""Admin OAuth2 mock flow routes.

This module provides a minimal, mock OAuth2 Authorization Code flow for the Admin Web Panel.
It validates client_id and redirect_uri against ADMIN_OAUTH_CLIENTS from settings, issues a short-lived
authorization code (in-memory), exchanges it for an admin-scoped JWT token, and exposes an /admin/me endpoint
to inspect the current admin user/session.

Endpoints:
- GET /oauth/authorize: Validates client and redirect_uri, returns 302 to redirect_uri with ?code=...&state=...
- POST /oauth/token: Exchanges code for JWT access_token (admin scope)
- GET /admin/me: Returns info about the admin token (requires Bearer token)

Notes:
- This is a MOCK implementation suitable for local development/testing. Do not use in production.
- Codes are stored in-memory and expire quickly.
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from src.api.config import OAuthClient, get_settings
from src.api.security import create_access_token, decode_access_token, oauth2_scheme

router = APIRouter()

# In-memory store for authorization codes for mock flow
# Maps code -> dict with client_id, redirect_uri, scope, expires_at
_AUTH_CODES: Dict[str, Dict[str, str]] = {}


def _find_oauth_client(client_id: str) -> Optional[OAuthClient]:
    """Find a configured admin OAuth client by client_id."""
    settings = get_settings()
    for c in settings.admin_oauth_clients:
        if c.client_id == client_id:
            return c
    return None


def _validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> bool:
    """In this mock, we require an exact match to the configured provider client's redirect URI.
    Since our OAuthClient model doesn't include redirect URIs, we accept any HTTPS URL by default for dev,
    but if ADMIN_OAUTH_CLIENTS entries include provider-specific redirect rules in future, enforce here.
    For safety in this mock, require scheme http(s) and non-empty.
    """
    return redirect_uri.startswith("http://") or redirect_uri.startswith("https://")


class TokenRequest(BaseModel):
    """Request model for exchanging authorization code for tokens."""
    grant_type: str = Field(..., description="Must be 'authorization_code'")
    code: str = Field(..., description="Authorization code obtained from /oauth/authorize")
    redirect_uri: str = Field(..., description="Redirect URI used during authorize")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")


class TokenResponse(BaseModel):
    """Response model for issued tokens."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration in seconds")
    scope: str = Field("admin", description="Granted scope(s)")


class AdminMeResponse(BaseModel):
    """Response for /admin/me containing token claims relevant to admin."""
    sub: str = Field(..., description="Subject")
    scope: str = Field(..., description="Scopes granted")
    iat: int = Field(..., description="Issued at (epoch seconds)")
    exp: int = Field(..., description="Expiry (epoch seconds)")
    nbf: int = Field(..., description="Not before (epoch seconds)")
    client_id: Optional[str] = Field(None, description="OAuth client id, if present")


# PUBLIC_INTERFACE
@router.get(
    "/oauth/authorize",
    summary="Mock OAuth2 Authorization endpoint",
    description="Validates client_id and redirect_uri, then redirects to redirect_uri with an authorization code and provided state.",
    tags=["auth"],
    responses={
        302: {"description": "Redirect to client with code/state"},
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized client"},
    },
)
async def oauth_authorize(
    request: Request,
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(..., description="Registered OAuth client ID"),
    redirect_uri: str = Query(..., description="Registered redirect URI for the client"),
    scope: str = Query("admin", description="Requested scopes space-delimited (mock supports 'admin')"),
    state: Optional[str] = Query(None, description="Opaque client state to be returned"),
) -> RedirectResponse:
    """Authorize endpoint for mock admin OAuth flow.

    On success, redirects to: redirect_uri?code=<code>&state=<state>
    """
    if response_type != "code":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported response_type")

    client = _find_oauth_client(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown client_id")

    if not _validate_redirect_uri(client, redirect_uri):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri")

    # Issue a short-lived authorization code
    code = secrets.token_urlsafe(24)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    _AUTH_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope or "admin",
        "expires_at": expires_at,
    }

    # Build redirect URL
    separator = "&" if ("?" in redirect_uri) else "?"
    url = f"{redirect_uri}{separator}code={code}"
    if state:
        url += f"&state={state}"

    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


# PUBLIC_INTERFACE
@router.post(
    "/oauth/token",
    summary="Exchange authorization code for JWT access token",
    description="Mock token exchange. Validates code, client, and redirect_uri; returns a JWT with admin scope.",
    tags=["auth"],
    response_model=TokenResponse,
    responses={
        200: {"description": "Access token issued"},
        400: {"description": "Invalid request"},
        401: {"description": "Invalid client or code"},
    },
)
async def oauth_token(payload: TokenRequest) -> TokenResponse:
    """Token endpoint for mock admin OAuth flow.

    Accepts authorization_code grant and returns a JWT bearer access_token with 'admin' scope.
    """
    if payload.grant_type != "authorization_code":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_grant_type")

    client = _find_oauth_client(payload.client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")

    # Optional: verify client_secret if provided in settings; our mock accepts any non-empty secret match.
    if client.client_secret and payload.client_secret != client.client_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client_secret")

    code_entry = _AUTH_CODES.get(payload.code)
    if not code_entry:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_code")

    # Validate redirect_uri matches original
    if code_entry.get("redirect_uri") != payload.redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri_mismatch")

    # Validate expiration
    try:
        exp_dt = datetime.fromisoformat(code_entry["expires_at"])
    except Exception:
        exp_dt = datetime.now(timezone.utc) - timedelta(seconds=1)
    if exp_dt < datetime.now(timezone.utc):
        # Remove expired code
        _AUTH_CODES.pop(payload.code, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="expired_code")

    # All good; consume the code (single-use)
    _AUTH_CODES.pop(payload.code, None)

    # Issue an admin-scoped JWT; for admin we can set a shorter expiry like 60 minutes or use settings default
    scope = code_entry.get("scope") or "admin"
    claims = {
        "sub": "admin",            # mock subject
        "scope": scope,            # 'admin'
        "client_id": payload.client_id,
        "role": "admin",
        "aud": "admin-panel",
    }
    token = create_access_token(claims)
    # Decode to fetch 'exp' and compute TTL for response
    decoded = decode_access_token(token)
    ttl = max(0, int(decoded["exp"] - decoded["iat"]))

    return TokenResponse(access_token=token, token_type="bearer", expires_in=ttl, scope=scope)


# PUBLIC_INTERFACE
@router.get(
    "/admin/me",
    summary="Get current admin identity",
    description="Returns information about the admin associated with the provided Bearer token.",
    tags=["auth"],
    response_model=AdminMeResponse,
    responses={
        200: {"description": "Admin info"},
        401: {"description": "Unauthorized"},
    },
)
async def admin_me(token: str = Depends(oauth2_scheme)) -> AdminMeResponse:
    """Returns the claims for the current admin token.

    Requires Authorization: Bearer <token> header.
    """
    payload = decode_access_token(token)
    # Basic scope check
    if payload.get("scope") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin_scope_required")

    return AdminMeResponse(
        sub=str(payload.get("sub", "")),
        scope=str(payload.get("scope", "")),
        iat=int(payload.get("iat", 0)),
        exp=int(payload.get("exp", 0)),
        nbf=int(payload.get("nbf", 0)),
        client_id=payload.get("client_id"),
    )
