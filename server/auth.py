"""Firebase Auth ID token verification and user authorization."""

import json
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

ALLOWED_EMAIL = os.environ.get("ALLOWED_EMAIL", "").strip().lower()


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    """Verify Firebase Auth Bearer token and check email against ALLOWED_EMAIL.

    In local development if FIREBASE_SA_JSON is not configured or DEV_MODE=true,
    returns mock user if authorization header is not provided.
    """
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"

    if not authorization:
        if dev_mode:
            return {"email": ALLOWED_EMAIL or "dev@example.com", "uid": "dev-user"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )

    token = parts[1]

    if dev_mode and token in ("mock-token", "dev"):
        return {"email": ALLOWED_EMAIL or "dev@example.com", "uid": "dev-user"}

    try:
        from firebase_admin import auth

        # Verify ID token
        decoded_token = auth.verify_id_token(token)
        email = (decoded_token.get("email") or "").strip().lower()

        if ALLOWED_EMAIL and email != ALLOWED_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for user {email}. Not authorized.",
            )

        return decoded_token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {e}",
        )

