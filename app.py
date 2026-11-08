import json
import os

import joblib
from fastapi import FastAPI

model = joblib.load("models/fraud_model.joblib")

# use the threshold from training if it's there, otherwise 0.5
THRESHOLD = 0.5
if os.path.exists("models/threshold.json"):
    with open("models/threshold.json") as f:
        THRESHOLD = json.load(f)["threshold"]

app = FastAPI(title="Card Fraud Scoring API")


@app.get("/health")
def health():
    return {"status": "ok", "threshold": THRESHOLD}
