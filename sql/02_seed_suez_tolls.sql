-- =============================================================================
-- SEED SUEZ TOLL RATES: Official SCA Progressive Tariff Cards (SDR per SCNT)
-- Source: Suez Canal Authority (SCA) Navigation Circulars
-- =============================================================================

INSERT INTO dim_suez_toll_rates (
    vessel_type, condition,
    tier_1_first_5k, tier_2_next_5k, tier_3_next_10k, tier_4_next_20k,
    tier_5_next_30k, tier_6_next_50k, tier_7_next_60k, tier_8_the_rest
) VALUES
-- Crude Oil Tankers
('Crude Oil Tankers', 'Laden', 11.04, 7.82, 5.91, 2.93, 2.53, 2.17, 2.13, 2.13),
('Crude Oil Tankers', 'Ballast', 9.40, 6.64, 5.04, 2.50, 2.14, 1.85, 1.82, 1.82),

-- Petroleum Products Tankers
('Petroleum Products Tankers', 'Laden', 11.04, 7.82, 5.91, 3.93, 3.84, 3.46, 3.34, 3.34),
('Petroleum Products Tankers', 'Ballast', 9.40, 6.64, 5.04, 2.50, 2.14, 1.85, 1.82, 1.82),

-- Dry Bulk Vessels
('Dry Bulk Vessels', 'Laden', 10.13, 7.74, 6.12, 2.24, 1.97, 1.85, 1.77, 1.77),
('Dry Bulk Vessels', 'Ballast', 8.62, 6.58, 5.21, 1.89, 1.68, 1.58, 1.50, 1.50),

-- Liquefied Petroleum Gas (LPG) Carriers
('Liquefied Petroleum Gas (LPG) Carriers', 'Laden', 11.60, 8.40, 6.22, 5.05, 4.42, 4.13, 4.13, 4.13),
('Liquefied Petroleum Gas (LPG) Carriers', 'Ballast', 9.87, 7.14, 5.29, 4.30, 3.76, 3.51, 3.51, 3.51),

-- Liquefied Natural Gas (LNG) Carriers
('Liquefied Natural Gas (LNG) Carriers', 'Laden', 10.42, 8.11, 7.02, 5.43, 5.03, 4.80, 4.67, 4.67),
('Liquefied Natural Gas (LNG) Carriers', 'Ballast', 8.87, 6.89, 5.97, 4.61, 4.27, 4.08, 3.97, 3.97),

-- Chemical Tankers & Liquid Bulk
('Chemical Tankers & Liquid Bulk', 'Laden', 11.55, 8.92, 7.12, 5.19, 4.63, 4.35, 4.27, 4.27),
('Chemical Tankers & Liquid Bulk', 'Ballast', 9.81, 7.58, 6.06, 4.42, 3.94, 3.70, 3.63, 3.63),

-- Container Ships (Includes specific 60k SCNT slab)
('Container Ships', 'Laden', 11.04, 7.58, 5.89, 4.13, 3.82, 3.01, 2.94, 2.88),
('Container Ships', 'Ballast', 9.40, 6.45, 5.00, 3.51, 3.25, 2.56, 2.52, 2.44),

-- General Cargo Vessels
('General Cargo Vessels', 'Laden', 10.08, 7.78, 5.42, 4.07, 3.94, 3.87, 3.80, 3.80),
('General Cargo Vessels', 'Ballast', 8.58, 6.62, 4.61, 3.45, 3.36, 3.30, 3.22, 3.22),

-- Roll-On/Roll-Off (Ro/Ro) Vessels
('Roll-On/Roll-Off (Ro/Ro) Vessels', 'Laden', 10.08, 7.50, 5.83, 4.21, 3.94, 3.80, 3.65, 3.65),
('Roll-On/Roll-Off (Ro/Ro) Vessels', 'Ballast', 8.58, 6.37, 4.97, 3.59, 3.36, 3.22, 3.12, 3.12),

-- Vehicles Carriers
('Vehicles Carriers', 'Laden', 11.04, 7.58, 5.67, 4.05, 3.82, 3.01, 2.88, 2.88),
('Vehicles Carriers', 'Ballast', 9.40, 6.45, 4.83, 3.45, 3.25, 2.56, 2.44, 2.44),

-- Cruise Ships
('Cruise Ships', 'Laden', 9.97, 7.00, 5.77, 4.08, 4.03, 3.90, 3.76, 3.76),
('Cruise Ships', 'Ballast', 8.48, 5.96, 4.91, 3.48, 3.42, 3.31, 3.19, 3.19),

-- Special Floating Units
('Special Floating Units', 'Laden', 11.98, 7.94, 7.14, 5.06, 4.76, 4.31, 4.16, 4.16),
('Special Floating Units', 'Ballast', 11.98, 7.94, 7.14, 5.06, 4.76, 4.31, 4.16, 4.16),

-- Other Vessels
('Other Vessels', 'Laden', 10.54, 7.10, 5.97, 4.35, 4.21, 3.94, 3.80, 3.80),
('Other Vessels', 'Ballast', 8.96, 6.04, 5.08, 3.70, 3.59, 3.36, 3.22, 3.22)
ON CONFLICT (vessel_type, condition) DO UPDATE SET
    tier_1_first_5k = EXCLUDED.tier_1_first_5k,
    tier_2_next_5k = EXCLUDED.tier_2_next_5k,
    tier_3_next_10k = EXCLUDED.tier_3_next_10k,
    tier_4_next_20k = EXCLUDED.tier_4_next_20k,
    tier_5_next_30k = EXCLUDED.tier_5_next_30k,
    tier_6_next_50k = EXCLUDED.tier_6_next_50k,
    tier_7_next_60k = EXCLUDED.tier_7_next_60k,
    tier_8_the_rest = EXCLUDED.tier_8_the_rest;
