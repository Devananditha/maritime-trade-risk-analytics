-- =============================================================================
-- MARITIME ROUTE RISK INTELLIGENCE: DATABASE DDL SCHEMA
-- Target Engines: PostgreSQL 14+ / DuckDB 1.0+
-- =============================================================================

-- 1. Dim Vessels: Vessel register, classification, capacity, and operational cost parameters
CREATE TABLE IF NOT EXISTS dim_vessels (
    mmsi BIGINT PRIMARY KEY,
    vessel_name VARCHAR(255),
    vessel_type VARCHAR(100),
    scnt NUMERIC(12, 2),
    dwt NUMERIC(12, 2),
    daily_charter_usd NUMERIC(12, 2),
    fuel_burn_tons_day NUMERIC(8, 2)
);

-- 2. Dim Ports: Global Container Port Performance Index (World Bank CPPI)
CREATE TABLE IF NOT EXISTS dim_ports (
    port_id BIGINT PRIMARY KEY,
    port_name VARCHAR(255) NOT NULL,
    un_locode VARCHAR(10),
    country VARCHAR(100),
    region VARCHAR(100),
    cppi_rank INT,
    cppi_score NUMERIC(10, 4),
    berth_efficiency_ratio NUMERIC(8, 4),
    annual_call_sample NUMERIC(10, 2)
);

-- 3. Dim Chokepoints: Strategic maritime corridors, spatial bounds, and economic benchmarks
CREATE TABLE IF NOT EXISTS dim_chokepoints (
    chokepoint_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    corridor VARCHAR(100),
    lat_min NUMERIC(8, 4) NOT NULL,
    lat_max NUMERIC(8, 4) NOT NULL,
    lon_min NUMERIC(8, 4) NOT NULL,
    lon_max NUMERIC(8, 4) NOT NULL,
    baseline_transit_hrs NUMERIC(8, 2),
    baseline_speed_knots NUMERIC(6, 2),
    base_toll_usd NUMERIC(14, 2),
    war_risk_surcharge_pct NUMERIC(6, 2),
    cape_diversion_added_days NUMERIC(6, 2)
);

-- 4. Dim Suez Toll Rates: Progressive SDR tariff brackets across vessel categories
CREATE TABLE IF NOT EXISTS dim_suez_toll_rates (
    vessel_type VARCHAR(100) NOT NULL,
    condition VARCHAR(20) NOT NULL,
    tier_1_first_5k NUMERIC(8, 4) NOT NULL,
    tier_2_next_5k NUMERIC(8, 4) NOT NULL,
    tier_3_next_10k NUMERIC(8, 4) NOT NULL,
    tier_4_next_20k NUMERIC(8, 4) NOT NULL,
    tier_5_next_30k NUMERIC(8, 4) NOT NULL,
    tier_6_next_50k NUMERIC(8, 4) NOT NULL,
    tier_7_next_60k NUMERIC(8, 4) DEFAULT 0.00,
    tier_8_the_rest NUMERIC(8, 4) NOT NULL,
    PRIMARY KEY (vessel_type, condition)
);

-- 5. Fact AIS Pings: High-frequency vessel telemetry observations
CREATE TABLE IF NOT EXISTS fact_ais_pings (
    ping_id BIGINT PRIMARY KEY,
    mmsi BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    sog_knots NUMERIC(6, 2),
    cog_degrees NUMERIC(6, 2),
    chokepoint_id INT
);

-- =============================================================================
-- PERFORMANCE INDEXES (B-Tree)
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_ais_coords ON fact_ais_pings (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_ais_mmsi_ts ON fact_ais_pings (mmsi, timestamp);
CREATE INDEX IF NOT EXISTS idx_ais_chokepoint ON fact_ais_pings (chokepoint_id);
CREATE INDEX IF NOT EXISTS idx_ports_locode ON dim_ports (un_locode);
