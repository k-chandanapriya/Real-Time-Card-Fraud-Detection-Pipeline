# Real-Time Card Fraud Detection Pipeline

A small version of how banks check card payments: transactions stream in through Kafka,
an XGBoost model scores each one through a FastAPI service, and a Streamlit dashboard
shows the fraud alerts live.

## How it works

```
 producer.py  --->  Kafka topic  --->  consumer.py  --->  FastAPI /score  (XGBoost)
 (replays test     "transactions"          |
  transactions)                            v
                                      SQLite (data/scored.db)
                                           |
                                           v
                                      dashboard.py  (Streamlit, refreshes every 2s)
```

1. **Producer** reads transactions from the test set and sends them to Kafka, 2 per second.
2. **Consumer** reads each message and calls the scoring API.
3. **API** builds the features, runs the model and returns a fraud probability.
4. **Consumer** saves the transaction and its score to SQLite.
5. **Dashboard** reads the database and shows metrics, latest alerts and the score trend.

Kafka sits in the middle so transactions can queue up safely if scoring is slow, and the
model lives behind an API so anything can reuse it, not just this pipeline.

## Results

Data: [Credit Card Transactions Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
(simulated). The train file covers an earlier time period than the test file, so the model is
tested on "future" transactions. Only 0.39% of test transactions are fraud.

Test set, 555,719 transactions, 2,145 of them fraud:

| Threshold | Precision (fraud) | Recall (fraud) | Alerts raised |
|-----------|------------------:|---------------:|--------------:|
| 0.5 (default) | 31.4% | 94.1% | 6,437 |
| **0.975 (tuned)** | **87.8%** | **77.0%** | 1,880 |

**PR-AUC: 0.874** (a random guess would get about 0.004)

Accuracy is 99.9% but that number means nothing here, since predicting "never fraud" already
gets 99.6%. The threshold is picked by best F1 on the last 20% of the training data (not
the test set). At 0.5 the model catches almost all fraud but two out of three alerts would
be a customer's card blocked for no reason, so the tuned threshold is the better trade-off.

Features used: amount, city population, hour of day, cardholder age, distance between the
cardholder and the merchant, merchant category and gender (see `features.py`).

## Project structure

```
├── data/                  # csvs from kaggle + scored.db (not in git)
├── models/                # trained model + threshold (not in git)
├── features.py            # feature engineering, used by both training and the api
├── train.py               # trains the model and picks the threshold
├── app.py                 # FastAPI scoring service
├── producer.py            # sends transactions to kafka
├── consumer.py            # reads from kafka, scores, saves to sqlite
├── dashboard.py           # streamlit dashboard
├── tests/test_api.py      # api tests
├── sample_transaction.json
├── Dockerfile
└── docker-compose.yml
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Mac, XGBoost also needs OpenMP: `brew install libomp`

Download the dataset from Kaggle (link above) and put `fraudTrain.csv` and `fraudTest.csv`
in `data/`.

## Train the model

```bash
python train.py
```

Takes under a minute on a laptop. Saves `models/fraud_model.joblib` and `models/threshold.json`.

## Run everything with Docker

After training:

```bash
docker compose up --build
```

- Dashboard: http://localhost:8501
- API docs: http://localhost:8000/docs

Stop with Ctrl+C, then `docker compose down`.

## Run locally without Docker

Start Kafka:

```bash
docker compose up -d kafka
```

Then in separate terminals (venv activated):

```bash
uvicorn app:app            # scoring api on :8000
python consumer.py         # waits for messages
python producer.py         # starts sending transactions
streamlit run dashboard.py # dashboard on :8501
```

Test the api with the sample transaction:

```bash
curl -X POST localhost:8000/score -H "Content-Type: application/json" -d @sample_transaction.json
```

Change `amt` to 12 and `category` to `grocery_pos` and the score drops a lot.

## Tests

```bash
pytest
```

## Dashboard

- Transactions scored, number of alerts and alert rate
- **Real fraud caught**: how many of the actual frauds got an alert (live recall)
- Latest 20 alerts and alerts by category
- Fraud score of the last 200 transactions
- A threshold slider in the sidebar to see how stricter or looser cutoffs change the alerts

The producer mixes in extra fraud (300 fraud + 3,000 normal) so alerts show up within the
first minute of the demo.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `NoBrokersAvailable` | Kafka is still starting, wait ~20 seconds |
| `FileNotFoundError: models/fraud_model.joblib` | Run `python train.py` first |
| `FileNotFoundError: data/fraudTest.csv` | Put the Kaggle csvs in `data/` |
| `422 Unprocessable Entity` | Request is missing a field, compare with `sample_transaction.json` |
| `libomp.dylib` error on Mac | `brew install libomp` |
| Dashboard stuck on "Waiting..." | Check the consumer is running and you started everything from the project folder |

## Next steps

- SHAP explanations for each score (why was this card flagged)
- Velocity features, like how many transactions a card made in the last hour
- Track experiments with MLflow
- Deploy the api and dashboard to the cloud
