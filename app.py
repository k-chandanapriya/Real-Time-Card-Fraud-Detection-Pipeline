import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from features import build_features

model = joblib.load("models/fraud_model.joblib")

# use the threshold from training if it's there, otherwise 0.5
THRESHOLD = 0.5
if os.path.exists("models/threshold.json"):
    with open("models/threshold.json") as f:
        THRESHOLD = json.load(f)["threshold"]

app = FastAPI(title="Card Fraud Scoring API")


class Transaction(BaseModel):
    trans_num: str
    trans_date_trans_time: str  # "2020-06-21 22:15:04"
    merchant: str
    category: str
    amt: float
    gender: str
    city_pop: int
    lat: float
    long: float
    merch_lat: float
    merch_long: float
    dob: str  # "1968-03-19"


@app.get("/health")
def health():
    return {"status": "ok", "threshold": THRESHOLD}


@app.post("/score")
def score(tx: Transaction):
    X = build_features(pd.DataFrame([tx.model_dump()]))
    p = float(model.predict_proba(X)[0, 1])
    return {
        "trans_num": tx.trans_num,
        "fraud_probability": round(p, 4),
        "is_fraud": p >= THRESHOLD,
    }
