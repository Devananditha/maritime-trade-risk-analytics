-- =============================================================================
-- SEED CHOKEPOINTS: Strategic Maritime Corridors and Geofence Bounding Boxes
-- =============================================================================

INSERT INTO dim_chokepoints (
    chokepoint_id, name, corridor,
    lat_min, lat_max, lon_min, lon_max,
    baseline_transit_hrs, baseline_speed_knots, base_toll_usd,
    war_risk_surcharge_pct, cape_diversion_added_days
) VALUES
(
    1, 'Suez Canal', 'Mediterranean - Red Sea Connector',
    29.8000, 31.3500, 32.2000, 32.7000,
    14.00, 8.50, 500000.00,
    15.00, 12.00
),
(
    2, 'Bab-el-Mandeb Strait', 'Southern Red Sea - Gulf of Aden',
    12.2000, 13.5000, 43.0000, 44.0000,
    6.00, 14.00, 0.00,
    125.00, 14.00
),
(
    3, 'Strait of Malacca', 'Indian Ocean - South China Sea',
    1.0000, 5.5000, 95.0000, 104.5000,
    32.00, 15.00, 0.00,
    2.50, 0.00
),
(
    4, 'Panama Canal', 'Atlantic - Pacific Gateway',
    8.8000, 9.4000, -80.1000, -79.5000,
    11.50, 6.00, 450000.00,
    0.00, 22.00
),
(
    5, 'Cape of Good Hope', 'South Atlantic - Indian Ocean Bypass',
    -36.5000, -33.5000, 17.5000, 21.0000,
    24.00, 13.50, 0.00,
    0.00, 0.00
)
ON CONFLICT (chokepoint_id) DO UPDATE SET
    name = EXCLUDED.name,
    corridor = EXCLUDED.corridor,
    lat_min = EXCLUDED.lat_min,
    lat_max = EXCLUDED.lat_max,
    lon_min = EXCLUDED.lon_min,
    lon_max = EXCLUDED.lon_max,
    baseline_transit_hrs = EXCLUDED.baseline_transit_hrs,
    baseline_speed_knots = EXCLUDED.baseline_speed_knots,
    base_toll_usd = EXCLUDED.base_toll_usd,
    war_risk_surcharge_pct = EXCLUDED.war_risk_surcharge_pct,
    cape_diversion_added_days = EXCLUDED.cape_diversion_added_days;
