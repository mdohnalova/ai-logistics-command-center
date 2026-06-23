# 📦 AI Logistics Command Center & ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

👉 **Live Production App:** [https://ai-logistics-command-center-7pl2ctmvivxpmldjafhh3x.streamlit.app/](https://ai-logistics-command-center-7pl2ctmvivxpmldjafhh3x.streamlit.app/)

> **A real-time data engineering pipeline and interactive management dashboard designed for modern supply chain operations.**  
> Automatically extracts messy shipment logs, executes complex data cleansing/transformations (ETL), isolates delivery anomalies, and serves a live dispatches command center for operations managers.

---

## 📈 Executive Summary

In logistics and supply chain management, data arrives from various external carriers, API webhooks, and warehouse scanners. This data is frequently malformed, contains duplicate entries, suffers from inconsistent timezones, and lacks proper formatting.

**Without an automated pipeline:**
- Logistics coordinators waste hours manually cross-checking delivery status discrepancies in Excel.
- Operational anomalies (e.g., massive delays, wrong shipping routes, volume spikes) are discovered too late, leading to expensive premium freight costs.
- Executive stakeholders have zero real-time visibility into operational metrics.

**This project solves it completely** by introducing a lightweight, enterprise-ready **ETL (Extract, Transform, Load) architecture** connected to an interactive Streamlit operational frontend.

---

## 🛠 How The ETL Architecture Works

The system architecture is strictly split into a high-performance **Data Engineering Backend Pipeline** and an **Operational Control Center UI**.


```

[Raw Carrier Logs] ──> shipments_input.csv
│
▼
┌──────────────────────────────────────────────────────────┐
│                      EXTRACTION & CLEANING               │
│                      backend: clean.py                   │
│ ──────────────────────────────────────────────────────── │
│  • Deduplicates shipment entries                        │
│  • Enforces unified UTF-8 & string column encoding       │
│  • Handles missing geographical/route values             │
└─────────────────────────────┬────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────┐
│                     DATA TRANSFORMATION                  │
│ ──────────────────────────────────────────────────────── │
│  • Calculates route transit times & delivery delays       │
│  • Flags operational anomalies (Critical delays, spikes) │
└─────────────────────────────┬────────────────────────────┘
│
▼
┌──────────────┴──────────────┐
▼                             ▼
[Data Science Export]           [Business BI Export]
logistics_output.json         logistics_output.csv
│                             │
└──────────────┬──────────────┘
│
▼
┌──────────────────────────────────────────────────────────┐
│                    STREAMLIT CONTROL DASHBOARD           │
│                    frontend: logistics_app.py            │
│ ──────────────────────────────────────────────────────── │
│  • Ingests clean data into st.session_state              │
│  • Displays real-time KPIs (Total shipments, delays)     │
│  • Live operational dispatcher control workspace         │
└──────────────────────────────────────────────────────────┘

```

---

## 🚀 Key Features

### 1. Data Engineering Pipeline (`clean.py`)
- **Robust ETL Processing** — Automated extraction of unorganized supplier data into a structured format.
- **Anomaly Detection engine** — Systematically flags shipments with irregular transit parameters, allowing operations to resolve friction points immediately.
- **Dual Engine Output** — Generates dense JSON payloads with operational metadata for engineering API consumptions, and standard flattened CSV files for immediate corporate reporting.

### 2. Interactive Operational Dashboard (`logistics_app.py`)
- **State-Driven Command Workspace** — Loads active dispatches into memory via `st.session_state`. Operators can instantly interact with individual shipments.
- **Dynamic Cross-Filtering** — Allows real-time filtering of massive logs based on status, carriers, delays, and critical levels instantly.
- **Advanced BI Visualizations** — Includes production-grade metrics, dynamic cargo distribution charts, and timeline graphs visualizing logistics performance.
- **One-Click Dispatcher Operations** — Simulates immediate delivery resolution. Clicking "Resolve Shipment" dynamically updates the database state and hot-reloads the application state via `st.rerun()`.

---

## 📊 Sample Visual Wireframe


```

┌────────────────────────────────────────────────────────────────────┐
│ 📦 AI Logistics Command Center — Dispatch Control Panel            │
├──────────┬─────────────────────────────────────────────────────────┤
│ 🎛 Filters│ 📦 Total Cargo: 124   🚨 Anomalies: 7   ⏱ Avg Transit: 4.2d│
│          │─────────────────────────────────────────────────────────│
│ Status   │ 📋 Active Shipment Queue (Filtered)                    │
│ [✓] Transit│ ┌────┬──────────────┬─────────────┬──────────┬────────┐ │
│ [✓] Delayed│ │ ID │ Carrier      │ Destination │ Status   │ Urgency│ │
│          │ ├────┼──────────────┼─────────────┼──────────┼────────┤ │
│ Urgency  │ │ 42 │ DHL Global   │ Munich, DE  │ DELAYED  │ CRITICAL│ │
│ [✓] High │ │ 43 │ FedEx Supply │ Prague, CZ  │ IN TRANS │ MEDIUM │ │
│ [✓] Medium│ │ 44 │ UPS Cargo    │ Vienna, AT  │ IN TRANS │ LOW    │ │
│          │ └────┴──────────────┴─────────────┴──────────┴────────┘ │
│ 📊 Vol.  │                                                         │
│ [Chart]  │ 🔍 Operational Dispatcher Action Panel                  │
│          │ Selected Shipment: [ Shipment #42 — DHL Global — Munich ]│
│ ⏱ Delays │ 📍 Route Status: Cargo delayed at borders due to weather│
│ [Chart]  │                                                         │
│          │ [ 🛠 Mark Issue Resolved & Release Shipment ]           │
└──────────┴─────────────────────────────────────────────────────────┘

```

---

## 📂 Project Repository Structure


```

ai-logistics-command-center/
│
├── clean.py                    # ETL pipeline (Extraction, Transformation, Cleansing)
├── logistics_app.py            # Streamlit Interactive Control Dashboard Web UI
├── requirements.txt            # Python dependencies configuration
│
├── shipments_input.csv         # Raw incoming carrier logs database
├── logistics_output.json       # Cleaned structured output payload for dev integration
└── logistics_output.csv        # Normalized tabular output file for Excel/PowerBI

```

---

## 🛠 Setup & Technical Execution

### 1. Local Installation
Clone the repository and deploy the required data-science packages into your environment:
```bash
git clone git clone https://github.com/mdohnalova/ai-logistics-command-center.git
(https://github.com/mdohnalova/ai-logistics-command-center.git)
cd ai-logistics-command-center
pip install -r requirements.txt

```

### 2. Run the Core ETL Pipeline

Execute the processing layer to load, sanitize, transform, and update the data warehouses:

```bash
python3 clean.py

```

### 3. Launch the Logistics Command Dashboard Locally

Spin up the real-time Streamlit executive UI application:

```bash
streamlit run logistics_app.py

```

*The local server will automatically spin up on your browser at `http://localhost:8501`.*

---

## 🚀 Future Business Scalability

* **Real-Time Webhook Engine** — Migrating from periodic batch CSV processing to asynchronous FastAPI endpoints accepting direct JSON webhooks from DHL/FedEx/UPS systems.
* **Predictive Arrival Core (AI)** — Integrating machine learning regressors to predict potential border delays before the vehicle leaves the warehouse.
* **Geospatial Route Mapping** — Implementing `st.map` tracking with live latitude and longitude telemetry streams.

---

## 👩‍💻 Author

**Martina Dohnalová**

AI Automation & Data Engineer

🌐 [Live App Production](https://ai-logistics-command-center-7pl2ctmvivxpmldjafhh3x.streamlit.app/)

*A specialized corporate portfolio piece showcasing advanced capabilities in building ETL data processing engines, automated business anomaly logic, and modern Streamlit decision-support web applications.*

```

---
