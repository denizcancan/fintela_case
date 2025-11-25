---

Your task is to design and implement a small system that processes Turkish fund data, manages investment portfolios, and computes analytical metrics (risk & performance) using data pipelines.

---

You will build:

1. **A Dagster data ingestion pipeline (**[https://docs.dagster.io](https://docs.dagster.io/)**)**
    
    Ingest Turkish fund data to PostgreSQL.
    
2. **A FastAPI service (**[https://fastapi.tiangolo.com](https://fastapi.tiangolo.com/)**)**
    
    CRUD for portfolios (group of funds) + risk and alert endpoints.
    
3. **Two analytics pipelines in Dagster**
    - Portfolio risk calculation
    - Fund performance evaluation

---

# **Quick Start**

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (if running locally without Docker)
- `uv` package manager ([install here](https://docs.astral.sh/uv/))

## Setup (One Command)

```bash
# Clone the repository
git clone <repository-url>
cd fintela-swe-case

# Run setup script (creates .env, starts Docker, loads data)
./scripts/setup.sh
```

That's it! All services will be running:
- **FastAPI**: http://localhost:8000
- **Dagster**: http://localhost:3000  
- **Dashboard**: http://localhost:5173

## Manual Setup

If you prefer to set up manually:

1. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Start Docker services**:
   ```bash
   docker-compose up -d
   ```

3. **Load fund_labels CSV**:
   ```bash
   uv run python scripts/init_db.py
   ```

4. **Create test portfolios** (optional):
   ```bash
   uv run python create_test_portfolios.py
   ```

## Database Tables

All tables are **automatically created** when PostgreSQL starts via Docker Compose:
- `portfolios` - Portfolio definitions
- `portfolio_positions` - Fund positions in portfolios
- `fund_labels` - Fund metadata (loaded from CSV)
- `fund_prices` - Daily fund prices (created by Dagster)
- `instrument_distributions` - Fund instrument distributions (created by Dagster)
- `portfolio_risk_scores` - Portfolio risk calculations
- `fund_performance_metrics` - Fund performance metrics

## Running Locally (Without Docker)

If you have PostgreSQL installed locally:

1. Create database:
   ```bash
   createdb fintela
   ```

2. Run SQL scripts:
   ```bash
   psql -d fintela -f portfolios.sql
   psql -d fintela -f risk_scores.sql
   psql -d fintela -f extra_indexes.sql
   ```

3. Update `.env` with your local PostgreSQL credentials

4. Load CSV:
   ```bash
   uv run python scripts/init_db.py
   ```

5. Start services:
   ```bash
   # FastAPI
   uv run python run_api.py

   # Dagster
   dagster dev
   ```

---

# **1. Background & Scenario**

Fintela works with Turkish asset managers who invest in a universe of funds.

They need a system that:

- Loads daily updated fund data (prices, category, instrument distribution)
- Allows definition of portfolios of funds (e.g. 25% FUNDX, 50% FUNDY, 25% FUNDZ)
- Computes portfolio risks daily
- Detects unusual behavior in individual funds
- Exposes results through a REST API

---

# **2. Requirements**

Below is the assignment in three parts. Both Dagster and FastAPI is python based, so Python is required. 
Also, please use virtual environemnts and uv as the package manager. (https://docs.astral.sh/uv/)

Use PostgreSQL as the target database of the dagster jobs, as well as the operational db that the FastAPI service uses.

---

## **2.1 Part A — Data Ingestion (Dagster)**

### **Your task**

Build a Dagster job that:

- Gets the data from the TEFAS website
- Parses fund, price, and instrument distribution data
- Upserts into PostgreSQL (idempotent)

> The fixed information about the funds are given with a csv under `data` folder, you can put that once to PostgreSQL to use in backend later. No need to write a job for the CSV. 
---

## **2.2 Part B — Portfolio Service (FastAPI)**

You will build a REST service that manages portfolios and exposes analytics. After building the service, create 50+ portfolios to use in the next step.

### **Endpoints to implement**

### **1. POST /portfolios**

Create a portfolio with positions:

```
{
	"id" : 1,
  "positions": [
    { "fund_code": "FUNDX", "weight": 0.25 },
    { "fund_code": "FUNDY", "weight": 0.50 },
    { "fund_code": "FUNDZ", "weight": 0.25 }
  ]
}
```

### **2. GET /portfolios**

List all portfolios 

### **3. GET /portfolios/{id}**

Return portfolio + positions.

### **4. PUT /portfolios/{id}**

Update name, positions.

### **5. DELETE /portfolios/{id}**

Delete portfolio

---

### **Risk & Alert Endpoints**

### **GET /portfolios/{id}/risk**

Returns latest risk:

```json
{
  "portfolio_id": 1,
  "risk_score": 0.92,
  "risk": "HIGH"
}
```

### **GET /alerts/portfolios**

Returns all portfolios with "HIGH" risk.

```json
[{
  "portfolio_id": 1,
  "risk_score": 0.92,
  "risk": "HIGH"
},
{
  "portfolio_id": 2,
  "risk_score": 0.04,
  "risk": "LOW"
}
]
```

### **GET /alerts/funds**

Returns funds that performs significantly bad compared to their peers.

```json
[{
  "fund_code": "ABC",
  "confidence": 0.89 // optional, confidence or a numeric value that signifies the strength of the change
}]
```

---

## **2.3 Part C — Analytics Pipelines (Dagster)**

You will build two jobs:

- portfolio_risk_job
- fund_performance_job

---

# **3. Analytics Specifications**

In this part, calculate quantitative metrics about the funds and  the portfolios. The calculations will be done with dagster jobs. The following definitions are somewhat vague but its intentional. There is not a single correct way of calculating those, also this  part is the open-ended, thought-provoking portion of the project that might be a little bit more fun then the rest. 

## **3.1 Portfolio Risk**

Fetch at least 180 trading days of prices for each fund (some may have less) for calculating a statistical “riskiness score”

You are free to come up with a measure of riskiness as long as it can be classified as LOW, MEDIUM or HIGH.

---

## **3.2 Fund Performance**

For each fund calculate how the fund is performing according to its peers and identify poor performers. Its peers can be understood as the funds with same category, similar asset distribution or any other method. One important consideration is that not producing many alerts.  

---

### **Optional but appreciated**

- README to document your approaches and thinking process in software design and analytics.
- Docker Compose setup
- Postman collection