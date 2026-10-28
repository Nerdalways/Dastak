import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

# Secret key for signing passes (override in production via environment variable)
GATE_PASS_SECRET = os.getenv("DASTAK_GATE_SECRET", "dastak_rwa_secret_key_2026")


def generate_gate_pass(
    vendor_id: str,
    name: str,
    category: str,
    canopy_number: int,
    society_id: str,
    duration_minutes: int = 45,
    verification_source: str = "e-Shram",
) -> Dict[str, Any]:
    """
    Generates a cryptographically signed, time-bound digital gate pass
    allowing a vendor verified entry for a specific operational window.
    """
    issued_at = int(time.time())
    expires_at = issued_at + (duration_minutes * 60)

    payload = {
        "v_id": vendor_id,
        "name": name,
        "category": category,
        "canopy": canopy_number,
        "society": society_id,
        "verified_by": verification_source,
        "iat": issued_at,
        "exp": expires_at,
    }

    # Canonical serialization
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = hmac.new(
        GATE_PASS_SECRET.encode("utf-8"),
        serialized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "pass_token": f"{serialized}.{signature}",
        "payload": payload,
        "signature": signature,
    }


def verify_gate_pass(pass_token: str) -> Dict[str, Any]:
    """
    Verifies an incoming digital gate pass presented to the society guard.
    Validates HMAC signature and operational time window.
    """
    try:
        serialized, signature = pass_token.rsplit(".", 1)
        expected_sig = hmac.new(
            GATE_PASS_SECRET.encode("utf-8"),
            serialized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {"valid": False, "reason": "TAMPERED_SIGNATURE"}

        payload = json.loads(serialized)
        current_time = int(time.time())

        if current_time > payload["exp"]:
            return {
                "valid": False,
                "reason": "PASS_EXPIRED",
                "expired_seconds_ago": current_time - payload["exp"],
            }

        return {"valid": True, "payload": payload}

    except Exception:
        return {"valid": False, "reason": "MALFORMED_TOKEN"}