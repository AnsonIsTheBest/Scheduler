"""
Auth dependency for /api/* routes.

The frontend sends `Authorization: Bearer <supabase access token>` on every
dashboard request (see src/lib/api.ts). This verifies that token against
your Supabase project's public signing key, fetched from their JWKS
endpoint — the correct approach for projects on Supabase's newer
asymmetric JWT Signing Keys (the ones that replaced the legacy shared
HS256 secret).

No secret to copy anywhere: the JWKS URL is derived from SUPABASE_URL,
which db.py already requires, so there's nothing new to configure in
Railway for this to work.
"""

import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

_supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
_jwks_url = f"{_supabase_url}/auth/v1/.well-known/jwks.json"

# Fetches once, caches, and re-fetches only if a token references a kid
# it hasn't seen before (e.g. after a key rotation).
_jwk_client = jwt.PyJWKClient(_jwks_url) if _supabase_url else None


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    if _jwk_client is None:
        raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured")

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            # Only asymmetric algorithms here, deliberately — never add
            # HS256 to this list. If HS256 were accepted, someone could
            # take this public key and use it as an HMAC secret to forge
            # a token that would still pass verification.
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    return payload  # payload["sub"] is the Supabase user id, if needed later
