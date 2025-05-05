# stock-index-screenr
## This is a containerized FastAPI application that builds and serves stock index data using DuckDB as the local database and Redis for caching.

## 🧱 Project Structure

#####├── app/
#####│ ├── main.py # FastAPI entrypoint
#####│ ├── database.py # DuckDB connection logic
#####│ ├── utils.py # Redis and utility functions
#####│ ├── index_builder.py # Business logic for index building
#####│ ├── models.py # (Optional) Data models
#####│ └── data/
#####│ └── index_data.duckdb # DuckDB file
#####├── Dockerfile
#####├── docker-compose.yml
#####└── requirements.txt



# Setup instructions (local + Docker):
### 🔧 Local Setup (Without Docker)

1. Create and activate virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run FastAPI server:

    ```bash
    uvicorn app.main:app --reload
    ```

---

### 🐳 Docker Setup

1. Ensure Docker Desktop is running.

2. Build and run the containers:

    ```bash
    docker-compose up --build
    ```

3. Access the API at:

    ```
    http://localhost:8000
    ```

    View Swagger UI at:

    ```
    http://localhost:8000/docs
    ```

---


§ Running data acquisition job:

python app/data_ingest.py

§ API usage (sample curl/Postman):
API End points :
1. POST - /build-index : 
2. GET - /indexperformance :
3. GET -/index-composition :
4. GET -/composition-changes :
5. POST -/export-data :

§ Database schema overview:
DB - index_data.duckdb
Tables :

stock_metadata
---------------
symbol (VARCHAR, PRIMARY KEY)
name (VARCHAR, NOT NULL)

daily_data
----------
symbol (VARCHAR, NOT NULL, FOREIGN KEY referencing stock_metadata.symbol)
date (DATE, NOT NULL)
market_cap (DOUBLE, NOT NULL)
price (DOUBLE, NOT NULL)
UNIQUE (symbol, date)

index_composition
-----------------
date (DATE, NOT NULL)
symbol (VARCHAR, NOT NULL, FOREIGN KEY referencing stock_metadata.symbol)
weight (DOUBLE, NOT NULL)
UNIQUE (date, symbol)

index_performance
-----------------
date (DATE, PRIMARY KEY)
index_value (DOUBLE, NOT NULL)
daily_return (DOUBLE)
cumulative_return (DOUBLE)

