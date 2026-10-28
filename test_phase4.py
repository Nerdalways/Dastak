import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.services.pool_service import evaluate_lane_dispatch, generate_audio_cue

print("==================================================")
print("--- TEST 1: SUB-THRESHOLD MICRO-ORDER (₹40, 1 Household) ---")
print("==================================================")
micro_orders = [
    {"household_id": "FLAT_402", "amount": 40.0, "items": "1 kg Aloo + Dhaniya"}
]
res1 = evaluate_lane_dispatch("ROHINI_SEC9_GALI_4", "ROHINI_SEC9", micro_orders)
print(f"Status: {res1['status']}")
print(f"Target: {res1['target_location']}")
print(f"Total Value: ₹{res1['total_order_value']} (Threshold: ₹{res1['min_value_required']})")
print(f"Guidance: {res1['operational_guidance']}\n")

print("==================================================")
print("--- TEST 2: POOLED DEMAND MET (₹180, 3 Households) ---")
print("==================================================")
pooled_orders = [
    {"household_id": "FLAT_101", "amount": 60.0, "items": "2 kg Pyaz"},
    {"household_id": "FLAT_203", "amount": 70.0, "items": "1 kg Tamatar + Matar"},
    {"household_id": "FLAT_304", "amount": 50.0, "items": "Tadka Combo Basket"}
]
res2 = evaluate_lane_dispatch("ROHINI_SEC9_GALI_4", "ROHINI_SEC9", pooled_orders)
print(f"Status: {res2['status']}")
print(f"Target: {res2['target_location']}")
print(f"Total Value: ₹{res2['total_order_value']} across {res2['unique_households']} households")
print(f"Guidance: {res2['operational_guidance']}\n")

print("==================================================")
print("--- TEST 3: HANDS-FREE EARPIECE AUDIO CUE ---")
print("==================================================")
cue = generate_audio_cue(
    vendor_name="Raju Bhaiya",
    customer_label="Sharma ji (Flat 304)",
    item_bundle="1 kg Tamatar + Mirchi",
    destination="Peepal Tree Nukkad",
    language="hi"
)
print(f"Spoken Cue:\n🔊 \"{cue['cue_text']}\"")
print("==================================================")
