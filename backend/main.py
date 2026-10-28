import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import msgspec
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Database, Schemas, Models & Services
from backend.database import get_db
from backend.models.schema import Vendor, ZoneSubscription
from backend.schemas.telemetry import TelemetryPing
from backend.services.allocation_service import (
    allocate_order_to_lane,
    get_live_zone_feed,
    register_active_worker,
    unregister_worker,
)
from backend.services.h3_service import get_h3_cell
from backend.services.pass_service import generate_gate_pass, verify_gate_pass
from backend.services.pool_service import evaluate_lane_dispatch, generate_audio_cue
from backend.services.push_service import dispatch_cell_transition_alerts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dastak_core")

decoder = msgspec.json.Decoder(TelemetryPing)


class InMemoryL1Cache:
    """Thread-safe ephemeral L1 cache fallback."""
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = value
        return True

    async def close(self) -> None:
        self._store.clear()


redis_client: Any = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        redis_client = client
        logger.info("Connected to external Redis instance.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Redis unavailable ({exc}). Using local in-memory L1 cache.")
        redis_client = InMemoryL1Cache()

    # Pre-seed one sample active cart so feed is never completely blank on cold boot
    register_active_worker(
        worker_id="V-DEL-1049",
        name="Raju Prasad (राजू भैया)",
        role="HAWKER",
        category="Fresh Vegetables",
        canopy_number=104,
        h3_res9="893da18c12bffff",
        zone="ROHINI_SEC9",
        active_bundle="Daily Staples (Aloo, Pyaz, Tamatar)"
    )

    yield

    if redis_client:
        await redis_client.close()
        logger.info("Cache client closed.")


app = FastAPI(
    title="Project Dastak API",
    version="0.6.0",
    description="Automated Hyper-local Allocation, Spatial Ingestion, and Gate Pass Protocol.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


# --------------------------------------------------------------------------
# ROOT / HEALTH
# --------------------------------------------------------------------------
@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict[str, Any]:
    return {
        "project": "Project Dastak",
        "engine": "Automated Allocation & Spatial Dispatch",
        "status": "Online",
        "docs": "/docs",
    }


# --------------------------------------------------------------------------
# AUTOMATED ALLOCATION & LIVE ZONE FEED
# --------------------------------------------------------------------------
@app.get("/api/v1/feed", status_code=status.HTTP_200_OK)
async def get_feed(zone: str = "ROHINI_SEC9") -> Any:
    """Returns dynamic, real-time active vendors & technicians for the resident PWA."""
    return get_live_zone_feed(zone)


class ShiftStartPayload(msgspec.Struct):
    worker_id: str
    name: str
    role: str  # 'HAWKER' or 'GIG_TECH'
    category: str
    zone: str
    canopy_number: int | None = None
    h3_res9: str | None = "893da18c12bffff"
    active_bundle: str | None = "STAPLES"


shift_start_decoder = msgspec.json.Decoder(ShiftStartPayload)


@app.post("/api/v1/shift/start", status_code=status.HTTP_200_OK)
async def start_shift(request: Request) -> Any:
    """Worker starts shift: auto-allocates into live zone routing pool & issues gate pass."""
    body = await request.body()
    try:
        data = shift_start_decoder.decode(body)
    except Exception:
        return Response(status_code=400, content='{"error": "Invalid shift payload"}', media_type="application/json")

    # Rate cards for gig technicians
    rate_card = []
    if data.role == "GIG_TECH":
        rate_card = [
            {"name": "Switch / Socket Replacement", "rate": "₹79"},
            {"name": "Ceiling Fan Regulator / Capacitor", "rate": "₹120"},
            {"name": "MCB Trip / Short Circuit Check", "rate": "₹149"}
        ]

    worker = register_active_worker(
        worker_id=data.worker_id,
        name=data.name,
        role=data.role,
        category=data.category,
        canopy_number=data.canopy_number or 104,
        h3_res9=data.h3_res9 or "893da18c12bffff",
        zone=data.zone,
        rate_card=rate_card,
        active_bundle=data.active_bundle or "STAPLES"
    )

    # Issue cryptographic gate pass
    pass_data = generate_gate_pass(
        vendor_id=data.worker_id,
        name=data.name,
        category=data.category,
        canopy_number=data.canopy_number or 104,
        society_id=data.zone,
        duration_minutes=60 if data.role == "HAWKER" else 120,
        verification_source="e-Shram Verified"
    )

    return {
        "status": "ALLOCATED_TO_ZONE",
        "worker": worker,
        "gate_pass": pass_data
    }


class ShiftEndPayload(msgspec.Struct):
    worker_id: str


shift_end_decoder = msgspec.json.Decoder(ShiftEndPayload)


@app.post("/api/v1/shift/end", status_code=status.HTTP_200_OK)
async def end_shift(request: Request) -> Any:
    """Worker ends shift: removes from active allocation pool."""
    body = await request.body()
    try:
        data = shift_end_decoder.decode(body)
    except Exception:
        return Response(status_code=400, content='{"error": "Invalid payload"}', media_type="application/json")

    unregister_worker(data.worker_id)
    return {"status": "DEALLOCATED", "worker_id": data.worker_id}


class AllocateOrderPayload(msgspec.Struct):
    lane_id: str
    zone: str
    household_id: str
    amount: float
    item_bundle: str


order_alloc_decoder = msgspec.json.Decoder(AllocateOrderPayload)


@app.post("/api/v1/orders/allocate", status_code=status.HTTP_200_OK)
async def handle_order_allocation(request: Request) -> Any:
    """Automated Order Allocation & Lane Demand Pooling."""
    body = await request.body()
    try:
        data = order_alloc_decoder.decode(body)
    except Exception:
        return Response(status_code=400, content='{"error": "Invalid order allocation payload"}', media_type="application/json")

    result = allocate_order_to_lane(
        lane_id=data.lane_id,
        zone=data.zone,
        household_id=data.household_id,
        amount=data.amount,
        item_bundle=data.item_bundle
    )
    return result


# --------------------------------------------------------------------------
# GATE PASS VERIFICATION
# --------------------------------------------------------------------------
class VerifyPassPayload(msgspec.Struct):
    pass_token: str


verify_decoder = msgspec.json.Decoder(VerifyPassPayload)


@app.post("/api/v1/gate-pass/verify", status_code=status.HTTP_200_OK)
async def check_vendor_pass(request: Request) -> Any:
    body = await request.body()
    try:
        data = verify_decoder.decode(body)
    except Exception:
        return Response(status_code=400, content='{"error": "Invalid pass token payload"}', media_type="application/json")
    return verify_gate_pass(data.pass_token)


# --------------------------------------------------------------------------
# TELEMETRY INGESTION
# --------------------------------------------------------------------------
@app.post("/api/v1/telemetry", status_code=status.HTTP_200_OK)
async def ingest_telemetry(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    body_bytes = await request.body()
    try:
        ping = decoder.decode(body_bytes)
    except Exception:
        return Response(status_code=400, content='{"error": "Validation failure"}', media_type="application/json")

    current_h3 = get_h3_cell(ping.lat, ping.lon)
    cache_key = f"vendor:{ping.v_id}:h3"
    prev_h3 = await redis_client.get(cache_key)

    if prev_h3 == current_h3:
        return {"status": "cell_unchanged", "h3": current_h3}

    await redis_client.set(cache_key, current_h3, ex=1800)

    stmt = select(ZoneSubscription).where(
        ZoneSubscription.h3_res9 == current_h3,
        ZoneSubscription.is_active.is_(True),
    )
    result = await db.execute(stmt)
    sub_records = list(result.scalars().all())

    subscriptions = [
        {"endpoint": s.endpoint, "p256dh": s.p256dh, "auth": s.auth}
        for s in sub_records
    ]

    vendor_meta = {
        "id": ping.v_id,
        "name": "Raju Bhaiya",
        "category": "Fresh Vegetables",
        "canopy_number": 104,
        "active_bundle": "STAPLES",
    }

    background_tasks.add_task(
        dispatch_cell_transition_alerts,
        current_h3,
        vendor_meta,
        subscriptions,
    )

    return {
        "status": "cell_transitioned",
        "prev_h3": prev_h3,
        "current_h3": current_h3,
        "subscribers_queued": len(subscriptions),
    }