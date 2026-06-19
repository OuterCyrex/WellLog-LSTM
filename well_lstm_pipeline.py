import glob
import os
import pickle
import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


TRAIN_DIR = r"data\train"
TEST_DIR = r"data\test"
FEATURE_COLUMNS = ["AC", "CAL", "GR", "DEN", "RT", "RXO"]
LABEL_COLUMN = "CNL"
CURVE_COLUMNS = FEATURE_COLUMNS + [LABEL_COLUMN]
LOG_COLUMNS = ["GR", "RT", "RXO"]
SEQ_LEN = 30
STEP = 1
HIDDEN_SIZE = 64
NUM_LAYERS = 2
DROPOUT = 0.2
LEARNING_RATE = 1e-3
BATCH_SIZE = 256
EPOCHS = 40
SEED = 2020
VAL_RATIO = 0.2
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def load_and_clean_well(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, skiprows=[1])
    df.columns = [
        "Well",
        "Dataset",
        "Depth",
        "AC",
        "CAL",
        "CNL",
        "DEN",
        "GR",
        "RT",
        "RXO",
    ]

    df["Depth"] = pd.to_numeric(df["Depth"], errors="coerce")
    for col in CURVE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.replace(-9999, np.nan, inplace=True)

    bounds = {
        "AC": (33, 180),
        "CAL": (0, 100),
        "CNL": (-5, 50),
        "DEN": (1.5, 3.01),
        "GR": (3, 500),
        "RT": (1, 10000),
        "RXO": (1, 10000),
    }
    for col, (low, high) in bounds.items():
        df[col] = df[col].clip(lower=low, upper=high)

    df = df.sort_values("Depth").reset_index(drop=True)
    df[CURVE_COLUMNS] = df[CURVE_COLUMNS].interpolate(
        method="linear", limit_direction="both"
    )
    df[CURVE_COLUMNS] = df[CURVE_COLUMNS].ffill().bfill()
    df = df.dropna(subset=["Depth"] + CURVE_COLUMNS).reset_index(drop=True)

    return df


def apply_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in LOG_COLUMNS:
        df[col] = np.log10(np.maximum(df[col].to_numpy(dtype=np.float64), 1e-9))
    return df


def load_well_group(data_dir: str) -> list[dict]:
    wells = []
    for file_path in sorted(glob.glob(os.path.join(data_dir, "*.csv"))):
        df = load_and_clean_well(file_path)
        if len(df) <= SEQ_LEN:
            continue
        df = apply_log_transform(df)
        wells.append(
            {
                "well_name": df.loc[0, "Well"],
                "file_path": file_path,
                "data": df,
            }
        )
    return wells


def split_train_val_wells(train_wells: list[dict], val_ratio: float) -> tuple[list[dict], list[dict]]:
    shuffled = train_wells[:]
    random.shuffle(shuffled)
    val_count = max(1, int(round(len(shuffled) * val_ratio)))
    val_wells = shuffled[:val_count]
    fit_wells = shuffled[val_count:]
    if not fit_wells:
        fit_wells = val_wells
        val_wells = shuffled[:1]
    return fit_wells, val_wells


def fit_scalers(train_wells: list[dict]) -> tuple[MinMaxScaler, MinMaxScaler]:
    train_x = np.vstack([well["data"][FEATURE_COLUMNS].to_numpy() for well in train_wells])
    train_y = np.vstack([well["data"][[LABEL_COLUMN]].to_numpy() for well in train_wells])

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    scaler_x.fit(train_x)
    scaler_y.fit(train_y)
    return scaler_x, scaler_y


def transform_well(df: pd.DataFrame, scaler_x: MinMaxScaler, scaler_y: MinMaxScaler) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = scaler_x.transform(df[FEATURE_COLUMNS].to_numpy())
    y = scaler_y.transform(df[[LABEL_COLUMN]].to_numpy())
    depth = df["Depth"].to_numpy()
    return x, y, depth


def create_sequences(x: np.ndarray, y: np.ndarray, depth: np.ndarray, seq_len: int, step: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_seq, y_seq, depth_seq = [], [], []
    for idx in range(0, len(x) - seq_len, step):
        x_seq.append(x[idx : idx + seq_len])
        y_seq.append(y[idx + seq_len])
        depth_seq.append(depth[idx + seq_len])
    return np.asarray(x_seq), np.asarray(y_seq), np.asarray(depth_seq)


def build_dataset(wells: list[dict], scaler_x: MinMaxScaler, scaler_y: MinMaxScaler) -> tuple[np.ndarray, np.ndarray]:
    x_parts = []
    y_parts = []
    for well in wells:
        x_scaled, y_scaled, depth = transform_well(well["data"], scaler_x, scaler_y)
        x_seq, y_seq, _ = create_sequences(x_scaled, y_scaled, depth, SEQ_LEN, STEP)
        if len(x_seq) == 0:
            continue
        x_parts.append(x_seq)
        y_parts.append(y_seq)

    if not x_parts:
        raise ValueError("No sequences were created. Check SEQ_LEN and cleaned data length.")

    return np.vstack(x_parts), np.vstack(y_parts)


@dataclass
class WellSequences:
    well_name: str
    depth: np.ndarray
    x: np.ndarray
    y: np.ndarray


def build_single_well_sequences(
    well: dict, scaler_x: MinMaxScaler, scaler_y: MinMaxScaler
) -> WellSequences:
    x_scaled, y_scaled, depth = transform_well(well["data"], scaler_x, scaler_y)
    x_seq, y_seq, depth_seq = create_sequences(x_scaled, y_scaled, depth, SEQ_LEN, STEP)
    return WellSequences(
        well_name=well["well_name"],
        depth=depth_seq,
        x=x_seq,
        y=y_seq,
    )


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


def make_loader(x: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
    dataset = TensorDataset(
        torch.tensor(x, dtype=torch.float32),
        torch.tensor(y, dtype=torch.float32),
    )
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def evaluate_loader(model: nn.Module, data_loader: DataLoader, criterion: nn.Module) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for x_batch, y_batch in data_loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)
            pred = model(x_batch)
            losses.append(criterion(pred, y_batch).item())
    return float(np.mean(losses)) if losses else 0.0


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    learning_rate: float,
) -> nn.Module:
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    best_state = None
    best_val_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        batch_losses = []
        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            optimizer.zero_grad()
            pred = model(x_batch)
            loss = criterion(pred, y_batch)
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())

        train_loss = float(np.mean(batch_losses)) if batch_losses else 0.0
        val_loss = evaluate_loader(model, val_loader, criterion)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
            }

        print(
            f"Epoch {epoch:03d}/{epochs:03d} "
            f"train_loss={train_loss:.6f} val_loss={val_loss:.6f}"
        )

    if best_state is not None:
        model.load_state_dict(best_state["model_state_dict"])
    return model


def inverse_label(values: np.ndarray, scaler_y: MinMaxScaler) -> np.ndarray:
    values = np.asarray(values).reshape(-1, 1)
    return scaler_y.inverse_transform(values).reshape(-1)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true).reshape(-1)
    y_pred = np.asarray(y_pred).reshape(-1)
    corr, _ = pearsonr(y_true, y_pred)
    return {
        "R": float(corr),
        "R2": float(r2_score(y_true, y_pred)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(mean_squared_error(y_true, y_pred, squared=False)),
    }


def predict_well(model: nn.Module, sequences: WellSequences, scaler_y: MinMaxScaler) -> dict:
    model.eval()
    x_tensor = torch.tensor(sequences.x, dtype=torch.float32, device=DEVICE)
    with torch.no_grad():
        pred_scaled = model(x_tensor).cpu().numpy().reshape(-1)

    y_true = inverse_label(sequences.y.reshape(-1), scaler_y)
    y_pred = inverse_label(pred_scaled, scaler_y)
    metrics = compute_metrics(y_true, y_pred)
    metrics["well_name"] = sequences.well_name
    metrics["num_samples"] = int(len(y_true))
    metrics["depth"] = sequences.depth
    metrics["y_true"] = y_true
    metrics["y_pred"] = y_pred
    return metrics


def summarize_metrics(results: list[dict]) -> tuple[dict, dict]:
    best = max(results, key=lambda item: item["R"])
    avg = {
        "R": float(np.mean([item["R"] for item in results])),
        "R2": float(np.mean([item["R2"] for item in results])),
        "MAE": float(np.mean([item["MAE"] for item in results])),
        "RMSE": float(np.mean([item["RMSE"] for item in results])),
    }
    return best, avg


def save_artifacts(model: nn.Module, scaler_x: MinMaxScaler, scaler_y: MinMaxScaler) -> None:
    torch.save(model.state_dict(), "models/well_lstm_model.pth")
    with open("models/scaler_x.pkl", "wb") as f:
        pickle.dump(scaler_x, f)
    with open("models/scaler_y.pkl", "wb") as f:
        pickle.dump(scaler_y, f)


def main() -> None:
    set_seed(SEED)
    train_wells = load_well_group(TRAIN_DIR)
    test_wells = load_well_group(TEST_DIR)

    if len(train_wells) < 2:
        raise ValueError("Need at least 2 training wells to split train and validation.")
    if not test_wells:
        raise ValueError("No test wells found.")

    fit_wells, val_wells = split_train_val_wells(train_wells, VAL_RATIO)
    scaler_x, scaler_y = fit_scalers(fit_wells)

    x_train, y_train = build_dataset(fit_wells, scaler_x, scaler_y)
    x_val, y_val = build_dataset(val_wells, scaler_x, scaler_y)

    train_loader = make_loader(x_train, y_train, BATCH_SIZE, shuffle=True)
    val_loader = make_loader(x_val, y_val, BATCH_SIZE, shuffle=False)

    model = LSTMRegressor(
        input_size=len(FEATURE_COLUMNS),
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT,
    ).to(DEVICE)

    model = train_model(model, train_loader, val_loader, EPOCHS, LEARNING_RATE)
    save_artifacts(model, scaler_x, scaler_y)

    results = []
    for well in test_wells:
        sequences = build_single_well_sequences(well, scaler_x, scaler_y)
        if len(sequences.x) == 0:
            continue
        result = predict_well(model, sequences, scaler_y)
        results.append(result)
        print(
            f"{result['well_name']}: "
            f"R={result['R']:.4f}, "
            f"R2={result['R2']:.4f}, "
            f"MAE={result['MAE']:.4f}, "
            f"RMSE={result['RMSE']:.4f}"
        )

    if not results:
        raise ValueError("No test sequences were created.")

    best, avg = summarize_metrics(results)
    print("\nBest test well")
    print(
        f"{best['well_name']}: "
        f"R={best['R']:.4f}, "
        f"R2={best['R2']:.4f}, "
        f"MAE={best['MAE']:.4f}, "
        f"RMSE={best['RMSE']:.4f}"
    )

    print("\nAverage across test wells")
    print(
        f"R={avg['R']:.4f}, "
        f"R2={avg['R2']:.4f}, "
        f"MAE={avg['MAE']:.4f}, "
        f"RMSE={avg['RMSE']:.4f}"
    )


if __name__ == "__main__":
    main()
