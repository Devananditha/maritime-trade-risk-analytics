# Maritime Route Risk Intelligence & Analytics Platform

An end-to-end data engineering and quantitative decision platform that evaluates real-time maritime corridor risks, quantifies supply chain vulnerability across strategic chokepoints, and models dynamic trade-offs between geopolitical transit surcharges and trans-oceanic routing alternatives.

---

## Executive Summary & Business Problem

Over 80% of global merchandise trade travels by sea, passing through vulnerable geographic bottlenecks including the Bab-el-Mandeb Strait / Red Sea, Suez Canal, Strait of Malacca, and Panama Canal. Recent geopolitical blockades, naval security zones, and canal draft limits have forced global shipping lines to make multi-million-dollar operational decisions:

* **The Transit Dilemma:** Pay volatile canal dues and war-risk insurance premiums (often surging $300,000 to $600,000+ per voyage) to transit high-risk straits.
* **The Diversion Dilemma:** Reroute vessels around the Cape of Good Hope, adding 10 to 14 days of transit time, burning hundreds of additional metric tons of bunker fuel, and accumulating inventory depreciation charges.

**Maritime Route Risk Intelligence** solves this dilemma by unifying high-frequency AIS spatial telemetry, global port dwell indices, and progressive canal tariff schedules into a unified analytics data mart and interactive risk simulation cockpit.

---

## Key System Capabilities

* **High-Throughput Spatial Telemetry Ingestion:** Processes millions of raw AIS pings across temporal windows using chunked memory streaming and spatial geofence indexing.
* **Chokepoint Vulnerability Index (CVI):** A composite risk algorithm ($0-100$) combining vessel deceleration, waiting area congestion density, and port dwell deviation.
* **Official Progressive Tariff Engine:** Full implementation of the official Suez Canal Authority (SCA) tiered Special Drawing Rights (SDR) tariff structures across 13 vessel categories in Laden and Ballast states.
* **Corridor Cost-Delta & Break-Even Simulator:** Dynamic trade-off engine computing the exact financial inflection point where diverting around Africa becomes more cost-effective than navigating high-risk corridors.
* **Dual-Engine OLAP Storage:** Embedded high-speed analytical queries via DuckDB for standalone execution, paired with an enterprise PostgreSQL relational star schema.

---

## System Architecture

```text
[RAW DATA INGESTION]
  AIS Telemetry (NOAA / DMA)          World Bank CPPI Port Annex          SCA Official Rate Circulars
  (~4.5M Pings / Day)                 (426 Global Ports)                  (13 Vessel Types / SCNT)
         │                                    │                                      │
         └──────────────────────┬─────────────┴──────────────────────────────────────┘
                                │
                                ▼
[DATA PROCESSING ENGINE]
  src/ingestion/stage_downloads.py (Auto-Stager)
  src/ingestion/ingest_ais.py (Spatial Filter)
  src/processing/pyspark_pipeline.py (Trajectory Windowing)
                                │
                                ▼
[DATA WAREHOUSE / STAR SCHEMA]
  ┌────────────────────────────────────────────────────────┐
  │ fact_ais_pings                   fact_voyages          │
  │ dim_vessels                      dim_ports (CPPI)      │
  │ dim_chokepoints                  dim_suez_toll_rates   │
  └────────────────────────────────────────────────────────┘
                 DuckDB (OLAP) / PostgreSQL
                                │
                                ▼
[ANALYTICS & SIMULATION LAYER]
  Chokepoint Vulnerability Index (CVI) Algorithm
  Dynamic Suez Progressive Toll Calculator (USD)
  Corridor Cost-Delta & Break-Even Decision Model
                                │
                                ▼
[EXECUTIVE DASHBOARD EXTRACTS]
  Tableau / Power BI Risk Cockpit Extracts
  Corridor Comparison Matrix & Bottleneck Heatmap
```

---

## Repository Structure

```text
maritime-trade-risk-analytics/
├── data/
│   ├── raw/
│   │   ├── dim_ports_clean.csv            # Standardized World Bank CPPI benchmarks
│   │   ├── dim_suez_toll_tiers.csv        # Progressive SCA tariff rate card
│   │   └── dim_chokepoints.csv            # Bounding boxes for global chokepoints
│   ├── processed/                         # Partitioned trajectory features & voyage extracts
│   └── maritime_risk.duckdb               # Embedded columnar OLAP database
├── sql/
│   ├── 01_schema.sql                      # Production PostgreSQL DDL with B-Tree indexes
│   ├── 02_seed_suez_tolls.sql             # SCA SDR progressive tariff seed data
│   ├── 03_seed_chokepoints.sql            # Strategic corridor geofences and baseline speed
│   └── 04_analytics_queries.sql           # CTEs for CVI score, carrier exposure & cost-delta
├── src/
│   ├── ingestion/
│   │   ├── stage_downloads.py             # Automatic discovery of downloads (~/Downloads)
│   │   ├── ingest_ais.py                  # Chunked streaming reader & coordinate validator
│   │   ├── ingest_cppi.py                 # World Bank CPPI Excel parser and cleaner
│   │   └── seed_reference_data.py         # Static dimension seeder
│   ├── processing/
│   │   └── pyspark_pipeline.py            # PySpark trajectory windowing & idle detection
│   ├── db/
│   │   └── db_loader.py                   # Unified DuckDB & PostgreSQL loader
│   ├── models/
│   │   ├── suez_calculator.py             # Dynamic SCA progressive toll engine (USD)
│   │   └── corridor_simulator.py          # Cape vs. Suez break-even simulation engine
│   └── app/
│       └── streamlit_cockpit.py           # Interactive scenario simulator prototype
├── tests/
│   ├── test_suez_calculator.py            # Tariff slab verification unit tests
│   ├── test_ingestion.py                  # Coordinate boundary and schema assertions
│   └── test_simulator.py                  # Financial break-even validation tests
├── requirements.txt                       # Project dependencies
├── run_phase1.py                          # Phase 1 pipeline execution driver
└── run_pipeline.py                        # Master pipeline execution driver
```

---

## Data Model (Relational Star Schema)

```text
[dim_ports]                              [dim_chokepoints]
├── port_id (PK)                         ├── chokepoint_id (PK)
├── port_name                            ├── name
├── un_locode                            ├── corridor
├── country                              ├── lat_min, lat_max, lon_min, lon_max
├── cppi_rank                            ├── baseline_speed_knots
└── berth_efficiency_ratio               └── war_risk_surcharge_pct
        │                                        │
        └───────────────────┬────────────────────┘
                            │
                            ▼
                      [fact_voyages]
                      ├── voyage_id (PK)
                      ├── mmsi (FK -> dim_vessels)
                      ├── origin_port_id (FK -> dim_ports)
                      ├── dest_port_id (FK -> dim_ports)
                      ├── chokepoint_id (FK -> dim_chokepoints)
                      ├── transit_duration_hrs
                      ├── total_fuel_cost_usd
                      ├── total_toll_usd
                      └── route_risk_score
                            ▲
                            │
                     [fact_ais_pings]
                      ├── ping_id (PK)
                      ├── mmsi (FK -> dim_vessels)
                      ├── timestamp
                      ├── latitude, longitude
                      ├── sog_knots, cog_degrees
                      └── chokepoint_id (FK)
```

---

## Core Analytical Models

### 1. Progressive Suez Canal Toll Calculation

SCA transit dues are structured in progressive tonnage brackets using Special Drawing Rights (SDR) and converted to USD:

$$\text{Transit Dues (USD)} = \left(\sum_{i=1}^{M} \text{Tonnage}_i \times \text{Rate}_i\right) \times \text{SDR\_to\_USD}$$

**Verified Calculation for an Ultra-Large Container Vessel (120,000 SCNT, Laden, SDR = $1.33 USD):**
* **First 5,000 SCNT:** $5,000 \times 11.04\text{ SDR} = 55,200.00\text{ SDR}$
* **Next 5,000 SCNT:** $5,000 \times 7.58\text{ SDR} = 37,900.00\text{ SDR}$
* **Next 10,000 SCNT:** $10,000 \times 5.89\text{ SDR} = 58,900.00\text{ SDR}$
* **Next 20,000 SCNT:** $20,000 \times 4.13\text{ SDR} = 82,600.00\text{ SDR}$
* **Next 30,000 SCNT:** $30,000 \times 3.82\text{ SDR} = 114,600.00\text{ SDR}$
* **Next 50,000 SCNT:** $50,000 \times 3.01\text{ SDR} = 150,500.00\text{ SDR}$
* **Total Base Dues:** $499,700.00\text{ SDR} \times 1.33 = \mathbf{\$664,601.00\text{ USD}}$

---

### 2. Chokepoint Vulnerability Index (CVI)

The CVI measures immediate transit bottleneck risk ($0-100$ scale):

$$\text{CVI} = w_1 \left(\frac{V_{\text{baseline}} - V_{\text{current}}}{V_{\text{baseline}}}\right) + w_2 \left(1 - \text{BER}_{\text{port}}\right) + w_3 (\text{Risk}_{\text{geo}})$$

Where $V$ is Speed Over Ground (SOG), $\text{BER}$ is the World Bank Berth Efficiency Ratio, and $\text{Risk}_{\text{geo}}$ is active insurance surcharge exposure.

---

### 3. Corridor Cost-Delta & Break-Even Formulation

The simulation model calculates the net economic variance between transiting the Suez Canal versus rerouting via the Cape of Good Hope:

$$\Delta\text{Cost} = \text{Cost}_{\text{Cape}} - \text{Cost}_{\text{Suez}}$$

$$\text{Cost}_{\text{Suez}} = \text{Base Toll} + \text{War Risk Premium} + (\text{Transit Days} \times \text{Daily Fuel Burn} \times P_{\text{fuel}})$$

$$\text{Cost}_{\text{Cape}} = 0\text{ Toll} + ((\text{Transit Days} + \Delta\text{Days}) \times (\text{Daily Fuel Burn} \times P_{\text{fuel}} + \text{Charter Rate})) + \text{Inventory Holding}$$

The model surfaces the **Break-Even War Risk Premium** where braving the chokepoint becomes economically irrational.

---

## Quickstart & Execution

### 1. Installation & Environment

```bash
git clone https://github.com/Devananditha/maritime-trade-risk-analytics.git
cd maritime-trade-risk-analytics
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the End-to-End Data Pipeline

The master runner discovers files from `~/Downloads`, extracts archives, runs validation, seeds schemas, loads DuckDB/Postgres, and prints analytical outputs:

```bash
python run_pipeline.py
```

### 3. Run Automated Tests

```bash
pytest -v tests/
```

### 4. Launch the Interactive Risk Simulation Cockpit

```bash
streamlit run src/app/streamlit_cockpit.py
```

---

## Sample Analytical Outputs

```text
========================================================================================
             MARITIME ROUTE RISK INTELLIGENCE - PIPELINE EXECUTION SUMMARY
========================================================================================
[INGESTION]
  ✔ Telemetry Stream: 4,521,890 AIS pings processed across target shipping lanes.
  ✔ Port Reference:   405 ports ingested from World Bank CPPI dataset.
  ✔ Tariff Registry:  13 vessel types / 8 tonnage tiers seeded from SCA rate circulars.

[MODEL VERIFICATION: SUEZ PROGRESSIVE TARIFFS]
  • Vessel:            Ultra-Large Container Ship (120,000 SCNT, Laden)
  • Base Transit Dues: 499,700.00 SDR
  • Net Transit Cost:  $664,601.00 USD (Exchange rate: 1.33 USD/SDR)

[CORRIDOR TRADE-OFF SIMULATION: ASIA TO NORTH EUROPE]
────────────────────────────────────────────────────────────────────────────────────────
Metric                           Suez Canal Corridor      Cape of Good Hope Diversion
────────────────────────────────────────────────────────────────────────────────────────
Transit Duration                 14.0 Days                26.0 Days (+12.0 Days)
Canal Toll Dues                  $664,601 USD             $0 USD
War Risk Insurance (0.35%)       $420,000 USD             $0 USD
Bunker Fuel Burn (VLSFO)         $1,092,000 USD           $2,028,000 USD (+$936,000)
Vessel Charter & Capital         $490,000 USD             $1,090,000 USD (+$600,000)
────────────────────────────────────────────────────────────────────────────────────────
Total Landed Voyage Cost         $2,666,601 USD           $3,118,000 USD
Cost Differential (Delta)        +$451,399 USD            (Suez Route currently more cost-effective)
Break-Even War Surcharge         > 0.72%                  (Inflection point where Cape route saves capital)
========================================================================================
```

---

## Technology Stack

* **Data Engineering & ETL:** Python, PySpark, Pandas, OpenPyXL
* **Analytical Databases:** DuckDB (In-process Columnar OLAP), PostgreSQL (Relational Star Schema)
* **Mathematical Modeling:** NumPy, SciPy (Optimization & Simulation)
* **Visualization & BI:** Tableau Desktop, Plotly, Streamlit
* **Quality Assurance & Testing:** PyTest (Unit & Pipeline assertions), Pydantic

---

## Authors & License

* **Lead Architect:** Devananditha V ([LinkedIn](https://www.linkedin.com/in/devanandithav2004) | [GitHub](https://github.com/Devananditha))
* **License:** Released under the [MIT License](LICENSE).
