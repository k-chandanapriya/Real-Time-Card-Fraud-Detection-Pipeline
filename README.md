# Real-Time Card Fraud Detection Pipeline

Scoring card transactions for fraud as they come in and showing alerts on a live dashboard.

Flow: `producer -> Kafka -> consumer -> FastAPI (XGBoost) -> SQLite -> dashboard`

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Mac, XGBoost also needs OpenMP: `brew install libomp`

Download the [Credit Card Transactions Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
from Kaggle and put `fraudTrain.csv` and `fraudTest.csv` in `data/`.

## Train the model

```bash
python train.py
```

Saves `models/fraud_model.joblib` and `models/threshold.json`.

## Run the pipeline

Start Kafka:

```bash
docker compose up -d kafka
```

Then in three terminals (venv activated):

```bash
uvicorn app:app        # scoring api on :8000
python consumer.py     # waits for messages
python producer.py     # starts sending transactions
```

The api docs are at http://localhost:8000/docs. You can also test it with the sample:

```bash
curl -X POST localhost:8000/score -H "Content-Type: application/json" -d @sample_transaction.json
```
