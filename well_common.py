import os
import pandas as pd
import numpy as np
import torch
from torch import nn

# Global Constants Definition
FEATURE_COLUMNS = ["AC", "CAL", "GR", "DEN", "RT", "RXO"]
LABEL_COLUMN = "CNL"
CURVE_COLUMNS = FEATURE_COLUMNS + [LABEL_COLUMN]
LOG_COLUMNS = ["GR", "RT", "RXO"]

# --- Model Architecture Configuration ---
SEQ_LEN = 30
STEP = 1
HIDDEN_SIZE = 128
NUM_LAYERS = 2
DROPOUT = 0.2


# The valid data bounds in  real physic world
BOUNDS = {
    "AC": (33, 180),
    "CAL": (0, 100),
    "CNL": (-5, 50),
    "DEN": (1.5, 3.01),
    "GR": (3, 500),
    "RT": (1, 10000),
    "RXO": (1, 10000),
}

# load *.csv file and clean the data
def load_and_clean_well(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, skiprows=[1])
    df.columns = ["Well", "Dataset", "Depth", "AC", "CAL", "CNL", "DEN", "GR", "RT", "RXO"]
    
    df["Depth"] = pd.to_numeric(df["Depth"], errors="coerce")
    for col in CURVE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    df.replace(-9999, np.nan, inplace=True)
    
    for col, (low, high) in BOUNDS.items():
        if col in df.columns:
            df[col] = df[col].clip(lower=low, upper=high)
            
    df = df.sort_values("Depth").reset_index(drop=True)
    df[CURVE_COLUMNS] = df[CURVE_COLUMNS].interpolate(method="linear", limit_direction="both")
    df[CURVE_COLUMNS] = df[CURVE_COLUMNS].ffill().bfill()
    df = df.dropna(subset=["Depth"] + CURVE_COLUMNS).reset_index(drop=True)
    return df

def apply_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in LOG_COLUMNS:
        df[col] = np.log10(np.maximum(df[col].to_numpy(dtype=np.float64), 1e-9))
    return df

# Create sliding windows' consequence 
def create_sequences(x: np.ndarray, y: np.ndarray, depth: np.ndarray, seq_len: int, step: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_seq, y_seq, depth_seq = [], [], []
    for idx in range(0, len(x) - seq_len, step):
        x_seq.append(x[idx : idx + seq_len])
        y_seq.append(y[idx + seq_len])
        depth_seq.append(depth[idx + seq_len])
    return np.asarray(x_seq), np.asarray(y_seq), np.asarray(depth_seq)

# LSTM model definition
class LSTMRegressor(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        output, _ = self.lstm(x, (h0, c0))
        output = self.dropout(output[:, -1, :])
        return self.fc(output)
