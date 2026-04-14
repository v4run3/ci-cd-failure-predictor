# Intelligent CI/CD Failure Predictor

An MLOps system that analyzes CI/CD pipeline logs and metadata to predict build failures before execution completes, providing early warnings and continuous improvement through new pipeline data.

---

## Project Structure

```
ci-cd-failure-predictor/
│
├── data/                  # Data storage
│   ├── raw/               # Raw ingested CI/CD logs and metadata
│   └── processed/         # Engineered features ready for training
│
├── ingestion/             # Data ingestion module
│   └── fetch_logs.py      # Fetch build logs from CI/CD providers
│
├── features/              # Feature engineering module
│   └── build_features.py  # Transform raw logs into ML features
│
├── model/                 # Machine learning module
│   ├── train.py           # Model training pipeline
│   ├── predict.py         # Inference / prediction logic
│   └── evaluate.py        # Model evaluation and metrics
│
├── api/                   # REST API service
│   └── main.py            # FastAPI app serving predictions
│
├── docker/                # Containerization
│   └── Dockerfile         # Docker image definition
│
├── k8s/                   # Kubernetes orchestration
│   ├── deployment.yaml    # K8s Deployment spec
│   └── service.yaml       # K8s Service spec
│
├── ci-cd/                 # CI/CD pipeline configs
│   └── placeholder.txt    # Reserved for GitHub Actions workflows
│
├── monitoring/            # Observability
│   └── prometheus.yml     # Prometheus scrape configuration
│
├── scripts/               # Utility scripts
│   └── retrain.py         # Model retraining orchestration
│
├── tests/                 # Test suite
│   └── test_basic.py      # Placeholder tests
│
├── notebooks/             # Exploratory analysis
│   └── exploration.ipynb  # Data exploration notebook
│
├── frontend/              # React dashboard (Vite)
│   ├── src/pages/         # Dashboard, Predict, History pages
│   ├── src/components/    # Reusable UI components
│   └── package.json       # Frontend dependencies
│
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation (this file)
```

---

## Status

**Frontend:** React Dashboard — Complete. Full dashboard with predict form, risk gauge, charts, dark mode.

### Quick Start

```bash
# Backend
pip install -r requirements.txt
python ingestion/fetch_logs.py       # generates data/raw/build_logs.csv
python features/build_features.py    # generates data/processed/features.csv
python model/train.py                # trains models, saves best to model/saved_model.pkl
python model/evaluate.py             # prints accuracy, F1, confusion matrix, etc.
python model/predict.py              # demo prediction on sample records
python scripts/retrain.py            # full retrain: new data → features → train → evaluate → compare
uvicorn api.main:app --port 8000     # start API server

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev                          # opens at http://localhost:5173
```

---

## Phases

1. **Phase 0** - Project skeleton — Done
2. **Phase 1** - Synthetic data generation and log ingestion — Done
3. **Phase 2** - Feature engineering pipeline — Done
4. **Phase 3** - Model training, evaluation, and prediction — Done
5. **Phase 4** - REST API for serving predictions
6. **Phase 5** - Docker containerization
7. **Phase 6** - Kubernetes deployment
8. **Phase 7** - CI/CD pipeline integration (GitHub Actions)
9. **Phase 8** - Monitoring, alerting, and model retraining — Done (retraining script)
