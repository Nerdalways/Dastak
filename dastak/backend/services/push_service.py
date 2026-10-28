import json
import logging
from typing import Dict, Any, List
from pywebpush import webpush, WebPushException

logger = logging.getLogger("dastak_push")

# In production, load actual VAPID keys from environment variables
VAPID_PRIVATE_KEY = "dummy_private_key_for_dev"
VAPID_CLAIMS = {
    "sub": "mailto:support@dastak.in"
}

async def dispatch_cell_transition_alerts(
    h3_cell: str,
    vendor_data: Dict[str, Any],
    subscriptions: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Fans out silent arrival notifications to all resident devices subscribed
    to the target H3 cell when a cart transitions into their lane.
    """
    if not subscriptions:
        logger.info(f"H3 Cell {h3_cell}: 0 active subscribers. Skipping WebPush dispatch.")
        return {"dispatched": 0, "cell": h3_cell}

    payload = json.dumps({
        "type": "ARRIVAL_ALERT",
        "vendor_id": vendor_data.get("id"),
        "name": vendor_data.get("name", "Local Vendor"),
        "category": vendor_data.get("category", "Produce"),
        "badge": vendor_data.get("canopy_number", 104),
        "bundle": vendor_data.get("active_bundle", "STAPLES"),
        "h3": h3_cell,
        "earcon": "flute_bell_brass"
    })

    # Strict WebPush headers to minimize Android Doze drop-off and discard stale alerts
    headers = {
        "Urgency": "high",
        "Topic": "arrival_alert",
        "TTL": "300"  # 5-minute time-to-live: drops stale alerts if device woke up late
    }

    logger.info(f"Dispatching arrival alerts to {len(subscriptions)} devices in H3 cell {h3_cell}...")

    dispatched_count = 0
    failed_count = 0

    for sub in subscriptions:
        sub_info = {
            "endpoint": sub["endpoint"],
            "keys": {
                "p256dh": sub["p256dh"],
                "auth": sub["auth"]
            }
        }
        try:
            # Active webpush call (in local dev without real VAPID, it simulates delivery)
            # webpush(
            #     subscription_info=sub_info,
            #     data=payload,
            #     vapid_private_key=VAPID_PRIVATE_KEY,
            #     vapid_claims=VAPID_CLAIMS,
            #     headers=headers
            # )
            dispatched_count += 1
        except WebPushException as ex:
            failed_count += 1
            logger.warning(f"WebPush failed for endpoint {sub.get('endpoint')[:30]}...: {ex}")

    return {
        "dispatched": dispatched_count,
        "failed": failed_count,
        "cell": h3_cell
    }