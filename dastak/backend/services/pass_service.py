import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

GATE_PASS_SECRET = os.getenv("GATE_PASS_SECRET", "DASTAK_RWA_SECURE_HMAC_KEY_2026").encode("utf-8")


def generate_gate_pass(
    vendor_id: str,
    name: str,
    category: str,
    canopy_number: int,
    society_id: str,
    duration_minutes: int = 45,
    verification_source: str = "e-Shram Verified"
) -> dict[str, Any]:
    iat = int(time.time())
    exp = iat + (duration_minutes * 60)

    payload = {
        "v_id": vendor_id,
        "name": name,
        "category": category,
        "canopy": canopy_number,
        "society": society_id,
        "verified_by": verification_source,
        "iat": iat,
        "exp": exp
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")

    signature = hmac.new(
        GATE_PASS_SECRET,
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    token = f"{payload_b64}.{signature}"

    return {
        "pass_token": token,
        "vendor_id": vendor_id,
        "name": name,
        "canopy_number": canopy_number,
        "category": category,
        "society_id": society_id,
        "issued_at": iat,
        "expires_at": exp,
        "valid_duration_minutes": duration_minutes,
        "verification_source": verification_source
    }


def verify_gate_pass(token: str) -> dict[str, Any]:
    if not token or "." not in token:
        return {"valid": False, "reason": "MALFORMED_TOKEN"}

    parts = token.strip().rsplit(".", 1)
    if len(parts) != 2:
        return {"valid": False, "reason": "MALFORMED_TOKEN"}

    payload_part, signature_received = parts[0], parts[1]

    try:
        padded_b64 = payload_part + "=" * (-len(payload_part) % 4)
        payload_json = base64.urlsafe_b64decode(padded_b64).decode("utf-8")
        payload_data = json.loads(payload_json)
        payload_b64 = payload_part
    except Exception:
        return {"valid": False, "reason": "MALFORMED_PAYLOAD"}

    expected_sig = hmac.new(
        GATE_PASS_SECRET,
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature_received):
        return {"valid": False, "reason": "INVALID_SIGNATURE"}

    now = int(time.time())
    if now > payload_data.get("exp", 0):
        return {"valid": False, "reason": "PASS_EXPIRED", "payload": payload_data}

    return {
        "valid": True,
        "status": "APPROVED",
        "payload": payload_data,
        "remaining_seconds": payload_data.get("exp", 0) - now
    }