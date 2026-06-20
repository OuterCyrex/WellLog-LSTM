import os
import json
import glob
import pickle
import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn

# Import shared logic and configuration
from well_common import (
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    load_and_clean_well,
    apply_log_transform,
    create_sequences,
    LSTMRegressor,
    SEQ_LEN,
    STEP,
    HIDDEN_SIZE,
    NUM_LAYERS,
    DROPOUT,
)

TEST_DIR = "data/test"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> None:
    print(DEVICE)

    # 1. Check if saved model and scalers exist
    model_path = "models/well_lstm_model.pth"
    scaler_x_path = "models/scaler_x.pkl"
    scaler_y_path = "models/scaler_y.pkl"

    if not (os.path.exists(model_path) and os.path.exists(scaler_x_path) and os.path.exists(scaler_y_path)):
        print("Error: Saved model or scaler files not found! Please run well_lstm_pipeline.py first to train the model.")
        return

    # 2. Load scalers
    with open(scaler_x_path, "rb") as f:
        scaler_x = pickle.load(f)
    with open(scaler_y_path, "rb") as f:
        scaler_y = pickle.load(f)
    print("Successfully loaded MinMaxScaler scalers.")

    # 3. Initialize and load model
    model = LSTMRegressor(
        input_size=len(FEATURE_COLUMNS),
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT,
    ).to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    print("Successfully loaded trained model weights.")

    # 4. Load test dataset
    test_files = sorted(glob.glob(os.path.join(TEST_DIR, "*.csv")))
    if not test_files:
        print(f"Error: No test CSV files found in {TEST_DIR}!")
        return
    print(f"Found {len(test_files)} test wells, starting predictions...")

    # 5. Predict and evaluate well by well
    output_data = {}
    for file_path in test_files:
        df_raw = load_and_clean_well(file_path)
        if len(df_raw) <= SEQ_LEN:
            print(f"Warning: Skipping well {file_path} due to insufficient data points (<= {SEQ_LEN})")
            continue
        
        well_name = df_raw.loc[0, "Well"]
        df_log = apply_log_transform(df_raw)
        
        # Scaling and Sequence creation
        x_scaled = scaler_x.transform(df_log[FEATURE_COLUMNS].to_numpy())
        y_scaled = scaler_y.transform(df_log[[LABEL_COLUMN]].to_numpy())
        depth = df_log["Depth"].to_numpy()
        
        x_seq, y_seq, depth_seq = create_sequences(x_scaled, y_scaled, depth, SEQ_LEN, STEP)
        
        # Inference
        x_tensor = torch.tensor(x_seq, dtype=torch.float32, device=DEVICE)
        with torch.no_grad():
            pred_scaled = model(x_tensor).cpu().numpy().reshape(-1)
        
        # Inverse Scaling
        y_true = scaler_y.inverse_transform(y_seq.reshape(-1, 1)).reshape(-1)
        y_pred = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(-1)
        
        # Calculate metrics
        corr = float(np.asarray(pearsonr(y_true, y_pred))[0])
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        print(f"\nWell: {well_name} prediction results:")
        print(f"  - Pearson R (趋势相关性): {corr:.4f}")
        print(f"  - R² (拟合优度):          {r2:.4f}")
        print(f"  - MAE (平均绝对误差):     {mae:.4f}")
        print(f"  - RMSE (均方根误差):      {rmse:.4f}")

        # Save structured results
        output_data[well_name] = {
            "metrics": {
                "R": float(corr),
                "R2": float(r2),
                "MAE": float(mae),
                "RMSE": float(rmse)
            },
            "depth": depth_seq.tolist(),
            "y_true": y_true.tolist(),
            "y_pred": y_pred.tolist()
        }

    # 6. Write output to JSON file
    output_path = "predictions.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"\nPrediction results and metrics successfully saved to: {output_path}")

if __name__ == "__main__":
    main()
