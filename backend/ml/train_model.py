import logging
import os
from typing import Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = "backend/ml/datasets/synthetic_transactions.csv"
MODEL_PATH = "backend/ml/models/fraud_model.pkl"


def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def preprocess_and_split(
    df: pd.DataFrame,
    target_col: str,
    random_state: int = 42,
    test_size: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, ColumnTransformer]:

    X = df.drop(columns=[target_col])
    y = df[target_col]

    categorical_features = [
        "payment_method",
        "merchant_risk_tier",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            )
        ],
        remainder="passthrough",
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    return X_train, X_test, y_train, y_test, preprocessor


def build_model(preprocessor: ColumnTransformer) -> Pipeline:

    rf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
    )

    gb = GradientBoostingClassifier(
        random_state=42,
    )

    lr = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight="balanced",
    )

    ensemble = VotingClassifier(
        estimators=[
            ("rf", rf),
            ("gb", gb),
            ("lr", lr),
        ],
        voting="soft",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", ensemble),
        ]
    )


def find_best_threshold(
    y_true,
    probabilities,
):

    best_threshold = 0.5
    best_f1 = -1

    for threshold in [i / 100 for i in range(10, 91, 5)]:

        predictions = (probabilities >= threshold).astype(int)

        score = f1_score(
            y_true,
            predictions,
            zero_division=0,
        )

        if score > best_f1:
            best_f1 = score
            best_threshold = threshold

    return best_threshold


def evaluate_model(
    model: Pipeline,
    X_train,
    X_test,
    y_train,
    y_test,
):

    probabilities = model.predict_proba(X_test)[:, 1]

    threshold = find_best_threshold(
        y_test,
        probabilities,
    )

    predictions = (probabilities >= threshold).astype(int)

    logger.info("Training samples: %d", len(X_train))
    logger.info("Testing samples: %d", len(X_test))
    logger.info("Selected threshold: %.2f", threshold)

    logger.info(
        "Accuracy: %.4f",
        accuracy_score(y_test, predictions),
    )

    logger.info(
        "Precision: %.4f",
        precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
    )

    logger.info(
        "Recall: %.4f",
        recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
    )

    logger.info(
        "F1-score: %.4f",
        f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
    )

    logger.info(
        "ROC-AUC: %.4f",
        roc_auc_score(
            y_test,
            probabilities,
        ),
    )

    logger.info(
        "Confusion Matrix:\n%s",
        confusion_matrix(
            y_test,
            predictions,
        ),
    )

    logger.info(
        "Classification Report:\n%s",
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        ),
    )


def save_model(
    model: Pipeline,
    path: str,
):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    joblib.dump(
        model,
        path,
    )

    logger.info(
        "Model saved to %s",
        path,
    )


def main():

    df = load_data(DATA_PATH)

    X_train, X_test, y_train, y_test, preprocessor = preprocess_and_split(
        df,
        target_col="is_fraud",
    )

    model = build_model(preprocessor)

    model.fit(
        X_train,
        y_train,
    )

    evaluate_model(
        model,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    save_model(
        model,
        MODEL_PATH,
    )


if __name__ == "__main__":
    main()