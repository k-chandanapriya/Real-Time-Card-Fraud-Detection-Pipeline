import json
import os
import sqlite3

import requests
from kafka import KafkaConsumer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
API_URL = os.getenv("API_URL", "http://localhost:8000")
DB_PATH = os.getenv("DB_PATH", "data/scored.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS scored (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trans_num TEXT UNIQUE,
        ts TEXT,
        merchant TEXT,
        category TEXT,
        amt REAL,
        fraud_probability REAL,
        is_fraud INTEGER,
        actual_fraud INTEGER
    )
""")

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers=BOOTSTRAP,
    group_id="fraud-scorer",
    auto_offset_reset="earliest",
    value_deserializer=lambda b: json.loads(b.decode("utf-8")),
)

for msg in consumer:
    tx = msg.value
    try:
        resp = requests.post(f"{API_URL}/score", json=tx, timeout=5)
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException as e:
        # don't crash the whole consumer because of one bad call
        print("could not score", tx.get("trans_num"), "-", e)
        continue

    conn.execute(
        """INSERT OR IGNORE INTO scored
           (trans_num, ts, merchant, category, amt, fraud_probability, is_fraud, actual_fraud)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (tx["trans_num"], tx["trans_date_trans_time"], tx["merchant"], tx["category"],
         tx["amt"], result["fraud_probability"], int(result["is_fraud"]), tx["is_fraud"]),
    )
    conn.commit()

    print("ALERT" if result["is_fraud"] else "ok   ", tx["trans_num"], result["fraud_probability"])
