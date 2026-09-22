"""Suez Canal Authority (SCA) Progressive Toll Rate Calculator.

Implements the official progressive tiered tariff formulas specified in official
SCA Navigation Circulars. Dues are calculated in Special Drawing Rights (SDR)
per Suez Canal Net Tonnage (SCNT) and converted to USD at prevailing exchange rates.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path for standalone execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.seed_reference_data import SUEZ_TOLL_TIERS_DATA

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("suez_calculator")

# Default alias mapping for vessel categories
VESSEL_TYPE_ALIASES: dict[str, str] = {
    "container": "Container Ships",
    "containers": "Container Ships",
    "container ship": "Container Ships",
    "container ships": "Container Ships",
    "crude": "Crude Oil Tankers",
    "crude oil": "Crude Oil Tankers",
    "crude oil tanker": "Crude Oil Tankers",
    "crude oil tankers": "Crude Oil Tankers",
    "product tanker": "Petroleum Products Tankers",
    "petroleum product": "Petroleum Products Tankers",
    "petroleum products": "Petroleum Products Tankers",
    "petroleum products tankers": "Petroleum Products Tankers",
    "bulk": "Dry Bulk Vessels",
    "dry bulk": "Dry Bulk Vessels",
    "dry bulk vessel": "Dry Bulk Vessels",
    "dry bulk vessels": "Dry Bulk Vessels",
    "lpg": "Liquefied Petroleum Gas (LPG) Carriers",
    "lpg carrier": "Liquefied Petroleum Gas (LPG) Carriers",
    "liquefied petroleum gas (lpg) carriers": "Liquefied Petroleum Gas (LPG) Carriers",
    "lng": "Liquefied Natural Gas (LNG) Carriers",
    "lng carrier": "Liquefied Natural Gas (LNG) Carriers",
    "liquefied natural gas (lng) carriers": "Liquefied Natural Gas (LNG) Carriers",
    "chemical": "Chemical Tankers & Liquid Bulk",
    "chemical tanker": "Chemical Tankers & Liquid Bulk",
    "chemical tankers & liquid bulk": "Chemical Tankers & Liquid Bulk",
    "general cargo": "General Cargo Vessels",
    "general cargo vessels": "General Cargo Vessels",
    "ro/ro": "Roll-On/Roll-Off (Ro/Ro) Vessels",
    "roro": "Roll-On/Roll-Off (Ro/Ro) Vessels",
    "roll-on/roll-off (ro/ro) vessels": "Roll-On/Roll-Off (Ro/Ro) Vessels",
    "vehicle": "Vehicles Carriers",
    "vehicles": "Vehicles Carriers",
    "car carrier": "Vehicles Carriers",
    "vehicles carriers": "Vehicles Carriers",
    "cruise": "Cruise Ships",
    "cruise ship": "Cruise Ships",
    "cruise ships": "Cruise Ships",
    "special": "Special Floating Units",
    "special floating units": "Special Floating Units",
    "other": "Other Vessels",
    "other vessels": "Other Vessels",
}


def normalize_vessel_type(vessel_type: str) -> str:
    """Normalize input vessel type string to the official SCA category name."""
    clean = vessel_type.strip().lower()
    if clean in VESSEL_TYPE_ALIASES:
        return VESSEL_TYPE_ALIASES[clean]
    for key, val in VESSEL_TYPE_ALIASES.items():
        if key in clean:
            return val
    return "Other Vessels"


def get_rate_card(vessel_type: str, is_laden: bool = True) -> dict[str, float]:
    """Retrieve the progressive tier rate card for a vessel type and condition."""
    norm_type = normalize_vessel_type(vessel_type)
    cond = "Laden" if is_laden else "Ballast"

    for entry in SUEZ_TOLL_TIERS_DATA:
        if entry["vessel_type"] == norm_type and entry["condition"] == cond:
            return entry

    # Fallback to other vessels if not found
    for entry in SUEZ_TOLL_TIERS_DATA:
        if entry["vessel_type"] == "Other Vessels" and entry["condition"] == cond:
            return entry

    raise ValueError(f"No rate card found for vessel type '{vessel_type}' under condition '{cond}'")


def calculate_suez_toll_breakdown(
    vessel_type: str,
    scnt_tonnage: float,
    is_laden: bool = True,
    sdr_to_usd: float = 1.33,
) -> dict[str, Any]:
    """Calculate detailed Suez Canal transit dues breakdown across all tiers.
    
    Returns breakdown of tonnages, rates, SDR dues per tier, total SDR, and total USD.
    """
    if scnt_tonnage < 0:
        raise ValueError("SCNT tonnage cannot be negative.")
    if scnt_tonnage == 0:
        return {
            "vessel_type": normalize_vessel_type(vessel_type),
            "condition": "Laden" if is_laden else "Ballast",
            "scnt_tonnage": 0.0,
            "tier_breakdown": [],
            "total_sdr": 0.0,
            "total_usd": 0.0,
            "sdr_to_usd_rate": sdr_to_usd,
        }

    norm_type = normalize_vessel_type(vessel_type)
    rate_card = get_rate_card(norm_type, is_laden=is_laden)

    # Progressive brackets specification:
    # 1: First 5,000 (0 - 5k)
    # 2: Next 5,000 (5k - 10k)
    # 3: Next 10,000 (10k - 20k)
    # 4: Next 20,000 (20k - 40k)
    # 5: Next 30,000 (40k - 70k)
    # 6: Next 50,000 (70k - 120k)
    # 7: Next 60,000 (120k - 180k) -> Container Ships specific bracket
    # 8: The Rest (>180k for containers, or >120k for standard)
    has_tier_7 = rate_card.get("tier_7_next_60k", 0.0) > 0.0 and norm_type == "Container Ships"

    tiers_config = [
        ("tier_1_first_5k", "First 5,000 SCNT", 5000.0, rate_card["tier_1_first_5k"]),
        ("tier_2_next_5k", "Next 5,000 SCNT", 5000.0, rate_card["tier_2_next_5k"]),
        ("tier_3_next_10k", "Next 10,000 SCNT", 10000.0, rate_card["tier_3_next_10k"]),
        ("tier_4_next_20k", "Next 20,000 SCNT", 20000.0, rate_card["tier_4_next_20k"]),
        ("tier_5_next_30k", "Next 30,000 SCNT", 30000.0, rate_card["tier_5_next_30k"]),
        ("tier_6_next_50k", "Next 50,000 SCNT", 50000.0, rate_card["tier_6_next_50k"]),
    ]

    if has_tier_7:
        tiers_config.append(("tier_7_next_60k", "Next 60,000 SCNT", 60000.0, rate_card["tier_7_next_60k"]))

    rest_rate = rate_card["tier_8_the_rest"]

    remaining_tonnage = float(scnt_tonnage)
    tier_breakdown = []
    total_sdr = 0.0

    for tier_key, label, max_capacity, rate in tiers_config:
        if remaining_tonnage <= 0:
            break
        applied_tonnage = min(remaining_tonnage, max_capacity)
        sdr_cost = applied_tonnage * rate
        total_sdr += sdr_cost
        remaining_tonnage -= applied_tonnage

        tier_breakdown.append({
            "tier_key": tier_key,
            "label": label,
            "tonnage": applied_tonnage,
            "rate_sdr": rate,
            "cost_sdr": round(sdr_cost, 4),
        })

    # Charge remaining tonnage under The Rest
    if remaining_tonnage > 0:
        sdr_cost = remaining_tonnage * rest_rate
        total_sdr += sdr_cost
        tier_breakdown.append({
            "tier_key": "tier_8_the_rest",
            "label": "The Rest (Excess Tonnage)",
            "tonnage": remaining_tonnage,
            "rate_sdr": rest_rate,
            "cost_sdr": round(sdr_cost, 4),
        })

    total_usd = total_sdr * sdr_to_usd

    return {
        "vessel_type": norm_type,
        "condition": "Laden" if is_laden else "Ballast",
        "scnt_tonnage": scnt_tonnage,
        "tier_breakdown": tier_breakdown,
        "total_sdr": round(total_sdr, 4),
        "total_usd": round(total_usd, 2),
        "sdr_to_usd_rate": sdr_to_usd,
    }


def calculate_suez_toll_usd(
    vessel_type: str,
    scnt_tonnage: float,
    is_laden: bool = True,
    sdr_to_usd: float = 1.33,
) -> float:
    """Production progressive toll calculator returning total transit dues in USD."""
    breakdown = calculate_suez_toll_breakdown(
        vessel_type=vessel_type,
        scnt_tonnage=scnt_tonnage,
        is_laden=is_laden,
        sdr_to_usd=sdr_to_usd,
    )
    return breakdown["total_usd"]


if __name__ == "__main__":
    # Test 120,000 SCNT Laden Container Ship
    ship_type = "Container Ships"
    scnt = 120000.0
    res = calculate_suez_toll_breakdown(ship_type, scnt, is_laden=True, sdr_to_usd=1.33)
    print(f"--- 120,000 SCNT Laden Container Ship Transit Dues ---")
    for t in res["tier_breakdown"]:
        print(f"  {t['label']}: {t['tonnage']:,.0f} SCNT @ {t['rate_sdr']} SDR = {t['cost_sdr']:,.2f} SDR")
    print(f"Total SDR: {res['total_sdr']:,.2f} SDR")
    print(f"Total USD: ${res['total_usd']:,.2f} USD")
