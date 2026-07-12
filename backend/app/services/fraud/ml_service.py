import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

class FraudPredictionResult:
    def __init__(self, fraud_probability: Optional[float], model_available: bool):
        self.fraud_probability = fraud_probability
        self.model_available = model_available

from pathlib import Path

class FraudMLService:
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Use pathlib to construct path relative to current file location
            base_path = Path(__file__).parent.parent.parent.parent
            self._model_path = base_path / "ml" / "models" / "fraud_model.pkl"
        else:
            self._model_path = Path(model_path)
        self._model = None

    def _load_model(self) -> None:
        if not self._model_path.exists():
            logger.warning(f"Model file not found at {self._model_path}")
            self._model = None
            return
        try:
            self._model = joblib.load(self._model_path)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")
            self._model = None

    def predict_probability(
        self,
        amount: float,
        hour_of_day: int,
        is_weekend: int,
        payment_method: str,
        is_international: int,
        merchant_risk_tier: str,
        merchant_age_days: int
    ) -> FraudPredictionResult:
        if self._model is None:
            self._load_model()
            if self._model is None:
                return FraudPredictionResult(fraud_probability=None, model_available=False)

        logger.info("Prediction started")

        # Construct DataFrame for model input
        input_df = pd.DataFrame([{
            "amount": amount,
            "hour_of_day": hour_of_day,
            "is_weekend": is_weekend,
            "payment_method": payment_method,
            "is_international": is_international,
            "merchant_risk_tier": merchant_risk_tier,
            "merchant_age_days": merchant_age_days
        }])

        try:
            proba = self._model.predict_proba(input_df)[:, 1][0]
            fraud_probability = round(proba * 100, 2)
            logger.info(f"Prediction completed, fraud probability: {fraud_probability}%")
            return FraudPredictionResult(fraud_probability=float(fraud_probability), model_available=True)
        except Exception as e:
            logger.warning(f"Prediction failed: {e}")
            return FraudPredictionResult(fraud_probability=None, model_available=False)