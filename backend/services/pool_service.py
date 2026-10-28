import logging
from typing import Any

logger = logging.getLogger("dastak_pool")

# Operational Thresholds
MIN_LANE_ORDER_VALUE: float = 150.0  # ₹150 minimum pooled cart detour
MIN_LANE_HOUSEHOLDS: int = 3  # OR 3 distinct households

# Canonical Anchor Points for Sub-Threshold Micro-Orders
DEFAULT_NUKKAD_ANCHORS: dict[str, str] = {
    "ROHINI_SEC9": "Sharma Chai Chowk (Corner of Gate 1 & Main Road)",
    "ROHINI_SEC9_GALI_4": "Peepal Tree Nukkad (Opposite Kirana Store)",
    "DEFAULT": "Main Road Corner Anchor Point",
}


def evaluate_lane_dispatch(
    lane_id: str, society_id: str, orders: list[dict[str, Any]]
) -> dict[str, Any]:
    """Evaluates pooled consumer reservations for a specific residential lane.

    Enforces the ₹150 MOV or 3-household threshold before approving a cart detour.
    """
    total_order_value: float = sum(float(o.get("amount", 0.0)) for o in orders)
    unique_households: int = len(
        {o.get("household_id") for o in orders if o.get("household_id")}
    )

    threshold_met = (
        total_order_value >= MIN_LANE_ORDER_VALUE
        or unique_households >= MIN_LANE_HOUSEHOLDS
    )

    if threshold_met:
        status = "DETOUR_APPROVED"
        target_location = f"{lane_id} (Doorstep Entry Approved)"
        guidance = "Cart cleared to enter inner residential alley."
    else:
        status = "ANCHOR_PICKUP"
        target_location = DEFAULT_NUKKAD_ANCHORS.get(
            lane_id,
            DEFAULT_NUKKAD_ANCHORS.get(
                society_id, DEFAULT_NUKKAD_ANCHORS["DEFAULT"]
            ),
        )
        guidance = (
            "Demand below threshold. Orders assigned to corner nukkad anchor."
        )

    return {
        "lane_id": lane_id,
        "society_id": society_id,
        "status": status,
        "threshold_met": threshold_met,
        "total_order_value": total_order_value,
        "unique_households": unique_households,
        "min_value_required": MIN_LANE_ORDER_VALUE,
        "min_households_required": MIN_LANE_HOUSEHOLDS,
        "target_location": target_location,
        "operational_guidance": guidance,
        "order_count": len(orders),
    }


def generate_audio_cue(
    vendor_name: str,
    customer_label: str,
    item_bundle: str,
    destination: str,
    language: str = "hi",
) -> dict[str, str]:
    """Synthesizes lightweight, hands-free vernacular audio text for vendor earpiece.

    Allows pre-bagging produce without unlocking or looking at the phone screen.
    """
    if language == "hi":
        cue_text = f"{destination}: {customer_label} ke liye {item_bundle} reserved hai. Kripya bag kar lein."
    else:
        cue_text = f"{destination}: {item_bundle} reserved for {customer_label}. Please pre-bag."

    return {
        "cue_text": cue_text,
        "language": language,
        "vendor": vendor_name,
        "audio_priority": "high",
    }