import json
import os
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "data/scored.db")

st.set_page_config(page_title="Fraud Monitor", layout="wide")
st.title("Real-time card fraud monitor")


def load_scored():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql("SELECT * FROM scored ORDER BY id", conn)
    except Exception:
        return pd.DataFrame()


def default_threshold():
    try:
        with open("models/threshold.json") as f:
            return float(json.load(f)["threshold"])
    except (OSError, KeyError, ValueError):
        return 0.5


# lets you see how many alerts you'd get with a stricter or looser cutoff
threshold = st.sidebar.slider("Alert threshold", 0.0, 1.0, default_threshold(), 0.01)
st.sidebar.caption("Starts at the threshold picked during training.")


@st.fragment(run_every=2)  # reruns this part every 2 seconds
def live_view():
    df = load_scored()
    if df.empty:
        st.info("Waiting for scored transactions...")
        return

    df["alert"] = df.fraud_probability >= threshold
    alerts = df[df.alert]
    caught = int((df.alert & (df.actual_fraud == 1)).sum())
    total_fraud = int(df.actual_fraud.sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions scored", len(df))
    c2.metric("Fraud alerts", len(alerts))
    c3.metric("Alert rate", f"{len(alerts) / len(df):.1%}")
    c4.metric("Real fraud caught", f"{caught} / {total_fraud}")

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Latest alerts")
        latest = alerts.sort_values("id", ascending=False).head(20)
        st.dataframe(
            latest[["ts", "merchant", "category", "amt", "fraud_probability", "actual_fraud"]],
            width="stretch",
            hide_index=True,
        )
    with right:
        st.subheader("Alerts by category")
        st.bar_chart(alerts.category.value_counts())

    st.subheader("Fraud score, last 200 transactions")
    st.line_chart(df.tail(200).set_index("id")["fraud_probability"])


live_view()
