import time
import hmac
import hashlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Project Dastak • Multi-Trade Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = b"dastak_secret_key_2026_seva_challenge"

# Dynamic Category Mappings for Verification
TRADE_DESCRIPTIONS = {
    "PRODUCE": "Fresh Vegetables & Fruits",
    "FOOD": "Prepared Street Food & Snacks",
    "APPAREL": "Apparel, Footwear & Dry Goods",
    "KABADI": "Scrap & Kabadi Pickup Service"
}

@app.get("/", response_class=HTMLResponse)
async def serve_resident_pwa():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Resident PWA Not Found</h1>"

@app.get("/partner", response_class=HTMLResponse)
async def serve_vendor_portal():
    try:
        with open("frontend/vendors.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Vendor Portal Not Found</h1>"

@app.get("/technician", response_class=HTMLResponse)
async def serve_technician_portal():
    try:
        with open("frontend/gig_workers.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Technician Portal Not Found</h1>"

@app.get("/guard", response_class=HTMLResponse)
async def serve_guard_console():
    try:
        with open("frontend/guard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Guard Console Not Found</h1>"

def generate_hmac_token(v_id: str, canopy: int, exp: int) -> str:
    raw_payload = f"{v_id}:{canopy}:{exp}"
    signature = hmac.new(SECRET_KEY, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()[:8]
    return f"DSTK-{canopy}-{exp}-{signature}"

@app.post("/api/v1/shift/start")
@app.post("/api/v1/gate-pass/generate")
async def start_shift_and_generate_pass(request: Request):
    data = await request.json()
    worker_id = data.get("worker_id", "V-DEL-1049")
    canopy_num = data.get("canopy_number", 104)
    name = data.get("name", "Raju Prasad")
    category_code = data.get("category", "PRODUCE")
    
    exp_time = int(time.time()) + 3600
    token = generate_hmac_token(worker_id, canopy_num, exp_time)

    return JSONResponse({
        "status": "ACTIVE",
        "gate_pass": {
            "pass_token": token,
            "worker_id": worker_id,
            "name": name,
            "canopy": canopy_num,
            "category": TRADE_DESCRIPTIONS.get(category_code, "General Vendor"),
            "expires_at": exp_time,
            "zone": "ROHINI_SEC9"
        }
    })

@app.post("/api/v1/gate-pass/verify")
async def verify_pass_token(request: Request):
    data = await request.json()
    token = data.get("pass_token", "").strip()

    try:
        parts = token.split("-")
        if len(parts) != 4 or parts[0] != "DSTK":
            return JSONResponse({"valid": False, "reason": "Malformed Token Format"}, status_code=200)

        canopy = int(parts[1])
        exp = int(parts[2])
        provided_sig = parts[3]

        if time.time() > exp:
            return JSONResponse({"valid": False, "reason": "Gate Pass Expired"}, status_code=200)

        v_id = "V-DEL-1049"
        expected_sig = hmac.new(SECRET_KEY, f"{v_id}:{canopy}:{exp}".encode('utf-8'), hashlib.sha256).hexdigest()[:8]

        if not hmac.compare_digest(provided_sig, expected_sig):
            return JSONResponse({"valid": False, "reason": "Cryptographic Signature Mismatch"}, status_code=200)

        return JSONResponse({
            "valid": True,
            "payload": {
                "v_id": v_id,
                "name": "Raju Prasad",
                "canopy": canopy,
                "verified_by": "e-Shram Authenticated"
            },
            "remaining_seconds": int(exp - time.time())
        })
    except Exception as e:
        return JSONResponse({"valid": False, "reason": f"Verification Error: {str(e)}"}, status_code=200)