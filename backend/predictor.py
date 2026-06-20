from __future__ import annotations

import io
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from well_common import (
    DROPOUT,
    FEATURE_COLUMNS,
    HIDDEN_SIZE,
    LABEL_COLUMN,
    LSTMRegressor,
    NUM_LAYERS,
    SEQ_LEN,
    STEP,
    apply_log_transform,
    create_sequences,
    load_and_clean_well,
)

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "well_lstm_model.pth"
SCALER_X_PATH = BASE_DIR / "models" / "scaler_x.pkl"
SCALER_Y_PATH = BASE_DIR / "models" / "scaler_y.pkl"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass
class PredictorArtifacts:
    model: torch.nn.Module
    scaler_x: object
    scaler_y: object


class WellLSTMPredictor:
    def __init__(self) -> None:
        self._artifacts: PredictorArtifacts | None = None

    @property
    def ready(self) -> bool:
        return self._artifacts is not None

    def load(self) -> None:
        if self._artifacts is not None:
            return
        if not (MODEL_PATH.exists() and SCALER_X_PATH.exists() and SCALER_Y_PATH.exists()):
            raise FileNotFoundError("Model artifacts are missing in models/.")

        with open(SCALER_X_PATH, "rb") as f:
            scaler_x = pickle.load(f)
        with open(SCALER_Y_PATH, "rb") as f:
            scaler_y = pickle.load(f)

        model = LSTMRegressor(
            input_size=len(FEATURE_COLUMNS),
            hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS,
            dropout=DROPOUT,
        ).to(DEVICE)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        model.eval()
        self._artifacts = PredictorArtifacts(model=model, scaler_x=scaler_x, scaler_y=scaler_y)

    def predict_dataframe(self, df_raw: pd.DataFrame) -> dict:
        self.load()
        if len(df_raw) <= SEQ_LEN:
            raise ValueError(f"Not enough rows. Need at least {SEQ_LEN + 1} valid samples.")

        df_log = apply_log_transform(df_raw)
        x_scaled = self._artifacts.scaler_x.transform(df_log[FEATURE_COLUMNS].to_numpy())
        y_scaled = self._artifacts.scaler_y.transform(df_log[[LABEL_COLUMN]].to_numpy())
        depth = df_log["Depth"].to_numpy()
        x_seq, y_seq, depth_seq = create_sequences(x_scaled, y_scaled, depth, SEQ_LEN, STEP)
        if len(x_seq) == 0:
            raise ValueError("Unable to build sequences from the uploaded file.")

        x_tensor = torch.tensor(x_seq, dtype=torch.float32, device=DEVICE)
        with torch.no_grad():
            pred_scaled = self._artifacts.model(x_tensor).cpu().numpy().reshape(-1)

        y_true = self._artifacts.scaler_y.inverse_transform(y_seq.reshape(-1, 1)).reshape(-1)
        y_pred = self._artifacts.scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(-1)

        if len(y_true) > 1:
            try:
                corr = float(np.asarray(pearsonr(y_true, y_pred))[0])
            except Exception:
                corr = float("nan")
            r2 = float(r2_score(y_true, y_pred))
        else:
            corr = float("nan")
            r2 = float("nan")

        metrics = {
            "R": corr,
            "R2": r2,
            "MAE": float(mean_absolute_error(y_true, y_pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        }
        well_name = str(df_raw.loc[0, "Well"]) if "Well" in df_raw.columns else "unknown"
        return {
            "well_name": well_name,
            "num_samples": int(len(y_true)),
            "metrics": metrics,
            "depth": depth_seq.tolist(),
            "y_true": y_true.tolist(),
            "y_pred": y_pred.tolist(),
        }

    def predict_bytes(self, file_bytes: bytes) -> dict:
        df_raw = load_and_clean_well(io.BytesIO(file_bytes))
        return self.predict_dataframe(df_raw)

    def predict_file(self, file_path: str | Path) -> dict:
        df_raw = load_and_clean_well(file_path)
        return self.predict_dataframe(df_raw)


predictor = WellLSTMPredictor()
