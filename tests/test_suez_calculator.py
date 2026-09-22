"""Unit tests for Suez Canal Progressive Toll Calculator."""

import pytest
from src.models.suez_calculator import (
    calculate_suez_toll_usd,
    calculate_suez_toll_breakdown,
    normalize_vessel_type,
)


def test_120k_laden_container_ship():
    """Verify exact output for a 120,000 SCNT Laden Container Ship.
    
    Formula verification:
    - First 5,000 SCNT @ 11.04 = 55,200 SDR
    - Next 5,000 SCNT @ 7.58 = 37,900 SDR
    - Next 10,000 SCNT @ 5.89 = 58,900 SDR
    - Next 20,000 SCNT @ 4.13 = 82,600 SDR
    - Next 30,000 SCNT @ 3.82 = 114,600 SDR
    - Next 50,000 SCNT @ 3.01 = 150,500 SDR
    Total SDR = 499,700.00 SDR
    Total USD (@ 1.33) = $664,601.00 USD
    """
    scnt = 120_000.0
    res = calculate_suez_toll_breakdown("Container Ships", scnt, is_laden=True, sdr_to_usd=1.33)
    assert res["total_sdr"] == 499700.0
    assert res["total_usd"] == 664601.0

    # Also test convenience function
    toll_usd = calculate_suez_toll_usd("Container Ships", scnt, is_laden=True, sdr_to_usd=1.33)
    assert toll_usd == 664601.0


def test_150k_container_ship_tier7_slab():
    """Verify container ship exceeding 120k utilizes the specific 60k slab (Order 7: 2.94 SDR)."""
    scnt = 150_000.0
    res = calculate_suez_toll_breakdown("Container Ships", scnt, is_laden=True, sdr_to_usd=1.33)
    # First 120k = 499,700 SDR. Next 30,000 @ 2.94 = 88,200 SDR. Total = 587,900 SDR.
    assert res["total_sdr"] == 499700.0 + 88200.0
    assert res["total_usd"] == round(587900.0 * 1.33, 2)


def test_ballast_discount_container_ship():
    """Ballast transit dues must be strictly lower than Laden condition."""
    scnt = 100_000.0
    laden_toll = calculate_suez_toll_usd("Container Ships", scnt, is_laden=True)
    ballast_toll = calculate_suez_toll_usd("Container Ships", scnt, is_laden=False)
    assert ballast_toll < laden_toll
    assert ballast_toll > 0


def test_crude_oil_tanker_calculation():
    """Verify calculation for Crude Oil Tanker across progressive slabs."""
    scnt = 50_000.0
    # First 5k @ 11.04 = 55,200
    # Next 5k @ 7.82 = 39,100
    # Next 10k @ 5.91 = 59,100
    # Next 20k @ 2.93 = 58,600
    # Next 10k (of 30k) @ 2.53 = 25,300
    # Total SDR = 55200 + 39100 + 59100 + 58600 + 25300 = 237,300 SDR
    res = calculate_suez_toll_breakdown("Crude Oil Tankers", scnt, is_laden=True, sdr_to_usd=1.0)
    assert res["total_sdr"] == 237300.0


def test_zero_and_negative_tonnage():
    """Zero tonnage returns 0.0 USD; negative tonnage raises ValueError."""
    assert calculate_suez_toll_usd("Container Ships", 0.0) == 0.0
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_suez_toll_usd("Container Ships", -500.0)


def test_vessel_type_aliases():
    """Vessel aliases should resolve to standardized SCA categories."""
    assert normalize_vessel_type("container") == "Container Ships"
    assert normalize_vessel_type("crude oil tanker") == "Crude Oil Tankers"
    assert normalize_vessel_type("bulk carrier") == "Dry Bulk Vessels"
    assert normalize_vessel_type("lng carrier") == "Liquefied Natural Gas (LNG) Carriers"
    assert normalize_vessel_type("unknown ship") == "Other Vessels"
