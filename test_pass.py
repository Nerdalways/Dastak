import sys
import os

# Ensure backend modules are discovered
sys.path.insert(0, os.path.abspath("."))

from backend.services.pass_service import generate_gate_pass, verify_gate_pass

print("--- 1. GENERATING DIGITAL GATE PASS ---")
pass_result = generate_gate_pass(
    vendor_id="V-DEL-1049",
    name="Raju Bhaiya",
    category="Fresh Vegetables",
    canopy_number=104,
    society_id="ROHINI_SEC9",
    duration_minutes=45,
    verification_source="e-Shram Verified"
)

token = pass_result["pass_token"]
print(f"Generated Pass Token:\n{token}\n")

print("--- 2. VERIFYING DIGITAL GATE PASS ---")
verification = verify_gate_pass(token)
print(f"Verification Result:\n{verification}\n")

print("--- 3. TESTING TAMPERED TOKEN ---")
tampered_token = token + "xyz"
tampered_result = verify_gate_pass(tampered_token)
print(f"Tampered Token Result:\n{tampered_result}\n")
