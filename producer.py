import json
import os
import time

import pandas as pd
from kafka import KafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
DELAY = float(os.getenv("SEND_DELAY", "0.5"))  # 0.5s = 2 transactions per second

COLS = ["trans_num", "trans_date_trans_time", "merchant", "category", "amt", "gender",
        "city_pop", "lat", "long", "merch_lat", "merch_long", "dob", "is_fraud"]

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

df = pd.read_csv("data/fraudTest.csv", usecols=COLS)

# real data is 0.5% fraud, so mix in more fraud to see alerts quickly in the demo
fraud = df[df.is_fraud == 1].sample(300, random_state=1)
normal = df[df.is_fraud == 0].sample(3000, random_state=1)
demo = pd.concat([fraud, normal]).sample(frac=1, random_state=1)

# is_fraud is the real label. the api ignores it, the dashboard uses it
for row in demo.to_dict(orient="records"):
    producer.send("transactions", row)
    print("sent", row["trans_num"], row["amt"])
    time.sleep(DELAY)

producer.flush()
print("done, sent", len(demo), "transactions")
