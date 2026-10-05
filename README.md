# CHRONOS
> A time-series security telemetry engine utilizing PyTorch Conv1D models for real-time anomaly detection.

## 🏗 System Architecture
CHRONOS is designed for low-latency execution boundary hardening. Telemetry is ingested via the FastAPI gateway, buffered in memory using Redis, and committed to InfluxDB 2.7 for long-term time-series storage. A PyTorch Convolutional 1D (Conv1D) model continuously analyzes this data stream to identify deviations in expected system telemetry, which are then visualized dynamically via Grafana.

## 🚀 Core Features
* **ML-Driven Detection:** PyTorch Conv1D architecture optimized for sequential time-series anomaly detection.
* **Asynchronous Telemetry Pipeline:** FastAPI and Redis integration prevents telemetry ingestion from blocking primary application threads.
* **Preflight Diagnostics:** Built-in `preflight.py` verification engine ensures all dependent data stores and models are fully operational before gateway initialization.

## 🛠 Tech Stack
* **Machine Learning:** PyTorch (Conv1D)
* **Backend/API:** Python, FastAPI
* **Infrastructure/Data:** InfluxDB 2.7, Redis, Grafana, Docker Compose

## ⚙️ Local Deployment & Execution
```bash
# 1. Clone the repository
git clone [https://github.com/Dannyo6/CHRONOS.git](https://github.com/Dannyo6/CHRONOS.git)
cd CHRONOS

# 2. Configure Environment variables
cp .env.example .env
# Edit .env with your specific InfluxDB tokens and credentials

# 3. Execute preflight diagnostics
python preflight.py

# 4. Boot the infrastructure
docker-compose up --build -d
```
