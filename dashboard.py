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


@st.fragment(run_every=2)  # reruns this part every 2 seconds
def live_view():
    df = load_scored()
    if df.empty:
        st.info("Waiting for scored transactions...")
        return

    alerts = df[df.is_fraud == 1]
    caught = int(((df.is_fraud == 1) & (df.actual_fraud == 1)).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions scored", len(df))
    c2.metric("Fraud alerts", len(alerts))
    c3.metric("Alert rate", f"{len(alerts) / len(df):.1%}")
    c4.metric("Real fraud caught", f"{caught} / {int(df.actual_fraud.sum())}")

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


live_view()
