import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import average_precision_score, classification_report, precision_recall_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from features import CATEGORICAL, build_features

train = pd.read_csv("data/fraudTrain.csv")
test = pd.read_csv("data/fraudTest.csv")

# the train file is in time order, so keep the last 20% aside to pick the threshold.
# the test file is only used once at the end
cut = int(len(train) * 0.8)
fit_part, val_part = train.iloc[:cut], train.iloc[cut:]

X_train, y_train = build_features(fit_part), fit_part["is_fraud"]
X_val, y_val = build_features(val_part), val_part["is_fraud"]
X_test, y_test = build_features(test), test["is_fraud"]

# only ~0.5% of rows are fraud, so give fraud rows more weight
ratio = (y_train == 0).sum() / (y_train == 1).sum()

prep = ColumnTransformer(
    [("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)],
    remainder="passthrough",
)

model = Pipeline([
    ("prep", prep),
    ("xgb", XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                          scale_pos_weight=ratio, eval_metric="aucpr")),
])
model.fit(X_train, y_train)

# pick the threshold with the best F1 on the validation part
val_proba = model.predict_proba(X_val)[:, 1]
precision, recall, thresholds = precision_recall_curve(y_val, val_proba)
f1 = 2 * precision * recall / (precision + recall + 1e-9)
best = np.argmax(f1[:-1])
threshold = float(thresholds[best])
print(f"threshold: {threshold:.3f}  (val precision {precision[best]:.3f}, recall {recall[best]:.3f})")

proba = model.predict_proba(X_test)[:, 1]
print("PR-AUC:", round(average_precision_score(y_test, proba), 4))
print(classification_report(y_test, proba >= threshold, digits=3))

joblib.dump(model, "models/fraud_model.joblib")
with open("models/threshold.json", "w") as f:
    json.dump({"threshold": round(threshold, 4)}, f)
print("saved models/fraud_model.joblib and models/threshold.json")
