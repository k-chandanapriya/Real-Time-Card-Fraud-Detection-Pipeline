import json
import os

import pytest

# the api loads the trained model on import, so skip if it hasn't been trained yet
if not os.path.exists("models/fraud_model.joblib"):
    pytest.skip("run train.py first", allow_module_level=True)

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

with open("sample_transaction.json") as f:
    SAMPLE = json.load(f)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_score_returns_probability():
    r = client.post("/score", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["trans_num"] == "test-001"
    assert 0 <= body["fraud_probability"] <= 1
    assert isinstance(body["is_fraud"], bool)


def test_small_grocery_scores_lower_than_big_online_purchase():
    small = dict(SAMPLE, amt=12.0, category="grocery_pos")
    big = client.post("/score", json=SAMPLE).json()["fraud_probability"]
    low = client.post("/score", json=small).json()["fraud_probability"]
    assert low < big


def test_bad_amount_is_rejected():
    r = client.post("/score", json=dict(SAMPLE, amt="not a number"))
    assert r.status_code == 422


def test_missing_field_is_rejected():
    bad = dict(SAMPLE)
    del bad["dob"]
    r = client.post("/score", json=bad)
    assert r.status_code == 422
