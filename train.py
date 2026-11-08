import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import average_precision_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from features import CATEGORICAL, build_features

train = pd.read_csv("data/fraudTrain.csv")
test = pd.read_csv("data/fraudTest.csv")

X_train, y_train = build_features(train), train["is_fraud"]
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

proba = model.predict_proba(X_test)[:, 1]
print("PR-AUC:", round(average_precision_score(y_test, proba), 4))
print(classification_report(y_test, proba >= 0.5, digits=3))

joblib.dump(model, "models/fraud_model.joblib")
print("saved models/fraud_model.joblib")
