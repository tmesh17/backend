"""
Supabase JWT verification for authenticated endpoints (e.g., POST /v0/reviews).

Uses the Supabase JWT secret to decode and verify the access token
sent from the frontend in the Authorization: Bearer header.
"""
import os
import jwt
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def verify_token(token: str) -> dict:
    """
    Decode and verify a Supabase JWT access token.
    Returns the decoded payload (includes 'sub' for user ID, 'email', etc.).
    Raises 401 if the token is missing, expired, or invalid.
    """
    if not SUPABASE_JWT_SECRET:
        # If no secret is configured, skip verification (dev/prototype mode)
        # In production, always require a valid secret.
        return {"sub": "dev-user", "email": "dev@example.com"}

    try:
        # Supabase uses HS256 for JWT signing
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase sets aud to "authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
