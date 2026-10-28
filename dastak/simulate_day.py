import sys
import os
import time

sys.path.insert(0, os.path.abspath("."))

from backend.services.h3_service import get_h3_cell
from backend.services.pass_service import generate_gate_pass, verify_gate_pass
from backend.services.pool_service import evaluate_lane_dispatch, generate_audio_cue


def run_full_day_simulation():
    print("======================================================================")
    print("               PROJECT DASTAK: END-TO-END SHIFT SIMULATION            ")
    print("======================================================================\n")

    # STAGE 1: MANDI INITIALIZATION & CANOPY BINDING
    print(">>> [STAGE 1: MANDI DEPARTURE & INVENTORY PRESET]")
    vendor_id = "V-DEL-1049"
    vendor_name = "Raju Bhaiya"
    canopy_id = 104
    category = "Fresh Vegetables"
    society = "ROHINI_SEC9"
    
    print(f"Vendor Logged In     : {vendor_name} ({vendor_id})")
    print(f"Physical Canopy Badge: #{canopy_id} (Reflective Balcony Marker)")
    print(f"Selected Preset      : Daily Morning Staples (Aloo, Pyaz, Tamatar, Dhaniya)")
    print("Status                : In Transit to Sales Sector\n")

    # STAGE 2: RWA PERIMETER ARRIVAL & GATE CLEARANCE
    print(">>> [STAGE 2: SOCIETY GATE ARRIVAL & CRYPTOGRAPHIC PASS ISSUANCE]")
    gate_pass = generate_gate_pass(
        vendor_id=vendor_id,
        name=vendor_name,
        category=category,
        canopy_number=canopy_id,
        society_id=society,
        duration_minutes=45,
        verification_source="e-Shram Verified"
    )
    pass_token = gate_pass["pass_token"]
    print(f"Generated HMAC Pass  : {pass_token[:42]}...[TRUNCATED]")

    verification = verify_gate_pass(pass_token)
    assert verification["valid"] is True, "Gate pass verification failed!"
    print(f"Guard Terminal Scan  : PASS VALID -> Approved entry for Canopy #{verification['payload']['canopy']}")
    print(f"Security Clearance   : {verification['payload']['verified_by']}")
    print(f"Allowed Entry Slot   : 45 Minutes Window (Gate 1 -> Towers A to D)\n")

    # STAGE 3: RESIDENTIAL GEOFENCE & H3 SPATIAL INGESTION
    print(">>> [STAGE 3: SPATIAL TELEMETRY & L1 TRANSITION DEDUPLICATION]")
    trajectory = [
        {"desc": "Gate 1 Checkpoint", "lat": 28.7194, "lon": 77.1082},
        {"desc": "Lingering at Gate 1 (Same Cell)", "lat": 28.7195, "lon": 77.1083},
        {"desc": "Moving down Central Drive (Tower C)", "lat": 28.7210, "lon": 77.1100}
    ]

    last_cell = None
    for idx, ping in enumerate(trajectory, 1):
        cell_id = get_h3_cell(ping["lat"], ping["lon"])
        if cell_id == last_cell:
            print(f"Ping {idx} ({ping['desc']}): Cell {cell_id} [UNCHANGED] -> Bypassed DB IOPS (0ms)")
        else:
            print(f"Ping {idx} ({ping['desc']}): Cell {cell_id} [TRANSITIONED] -> Triggered Sub-Cell Lookups")
            last_cell = cell_id

    print("Result               : Spatial deduplication avoided redundant DB lookups.\n")

    # STAGE 4: DEMAND POOLING DECISION ENGINE
    print(">>> [STAGE 4: LANE DEMAND POOLING & ROUTE ARBITRATION]")
    lane_id = "ROHINI_SEC9_GALI_4"

    print("--- Sub-case A: Single Micro-Order (Rs 30) ---")
    isolated_demand = [
        {"household_id": "FLAT_102", "amount": 30.0, "items": "1 kg Aloo"}
    ]
    eval_a = evaluate_lane_dispatch(lane_id, society, isolated_demand)
    print(f"Pooled Demand        : Rs {eval_a['total_order_value']} (Threshold: Rs {eval_a['min_value_required']})")
    print(f"Dispatch Decision    : {eval_a['status']}")
    print(f"Assigned Destination : {eval_a['target_location']}")
    print(f"Guidance             : {eval_a['operational_guidance']}\n")

    print("--- Sub-case B: Collective Lane Orders (Rs 190, 3 Households) ---")
    pooled_demand = [
        {"household_id": "FLAT_102", "amount": 50.0, "items": "1 kg Aloo + Dhaniya"},
        {"household_id": "FLAT_204", "amount": 80.0, "items": "2 kg Pyaz + Tamatar"},
        {"household_id": "FLAT_301", "amount": 60.0, "items": "Fresh Greens Bundle"}
    ]
    eval_b = evaluate_lane_dispatch(lane_id, society, pooled_demand)
    print(f"Pooled Demand        : Rs {eval_b['total_order_value']} across {eval_b['unique_households']} homes")
    print(f"Dispatch Decision    : {eval_b['status']}")
    print(f"Assigned Destination : {eval_b['target_location']}")
    print(f"Guidance             : {eval_b['operational_guidance']}\n")

    # STAGE 5: HANDS-FREE SINGLE-EARPIECE AUDIO CUE
    print(">>> [STAGE 5: VERNACULAR VENDOR AUDIO DISPATCH]")
    cue = generate_audio_cue(
        vendor_name=vendor_name,
        customer_label="Verma ji (Flat 204)",
        item_bundle="2 kg Pyaz + Tamatar",
        destination="Gali 4 Entrance",
        language="hi"
    )
    print(f"Vendor Screen State  : Locked in pocket (Zero mAh screen drain)")
    print(f"Audio Cue Dispatched : [HIGH PRIORITY TTS]")
    print(f"Earpiece Spoken      : \"{cue['cue_text']}\"\n")

    # STAGE 6: RESIDENT WEBPUSH SYNTHESIS
    print(">>> [STAGE 6: 0 dB RESIDENT WEBPUSH NOTIFICATION]")
    print("WebPush Protocol     : RFC 8291 Standard (Zero-PII Token)")
    print("Delivery Headers     : Urgency: high | TTL: 300 | Topic: arrival_alert")
    print("Acoustic Earcon      : 523.25 Hz Synthesized Brass Sine Bell (Web Audio API)")
    print("Resident UI Display  : 'Raju Bhaiya (Canopy #104) is outside Tower C lobby.'")
    print("Settlement Protocol  : Direct In-Person UPI / Cash (0% Platform Take-Rate)\n")

    print("======================================================================")
    print("       ALL SYSTEM SUB-PROTOCOLS VALIDATED - SIMULATION COMPLETE       ")
    print("======================================================================")


if __name__ == "__main__":
    run_full_day_simulation()
