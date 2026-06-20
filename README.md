# WellLog-LSTM

A deep learning project using an LSTM (Long Short-Term Memory) network to reconstruct well log curves (reconstructing the `CNL` curve using `AC`, `CAL`, `GR`, `DEN`, `RT`, and `RXO` features).

## 1. Installation

This project uses **uv** for environment and dependency management. The base dependencies (required for prediction/inference) include `torch`, `pandas`, `numpy`, `scipy`, and `scikit-learn`. `matplotlib` (used for plotting and training analysis) is optional and configured under the `train` extra.

To set up the virtual environment:

* **For Prediction (Default)**: Installs only the core libraries required for running predictions:
  ```bash
  uv sync
  ```

* **For Training**: Installs core libraries plus optional training/plotting packages (`matplotlib`):
  ```bash
  uv sync --extra train
  ```

Alternatively, you can install the dependencies manually using `uv pip`:

```bash
# Default (predict)
uv pip install -e .

# With training extras
uv pip install -e ".[train]"
```

## 2. Data Directory Structure

Data files are excluded from Git via `.gitignore`. Before running the scripts, create a `data` directory in the project root and place your `.csv` files inside:

```text
WellLog-LSTM/
└── data/
    ├── train/      # CSV files of wells used for training and validation
    └── test/       # CSV files of wells used for testing and evaluation
```

*Note: The first row of the CSV files should be the column headers. The second row (if it contains units) is automatically skipped by the data loader. Invalid values should be represented as `-9999`.*

## 3. Running the Project

The core data preprocessing, window segmentation, and model architecture are modularized inside [well_common.py](well_common.py).

### Step 1: Train the Model
To clean the raw logs, split the data into training and validation sets, train the LSTM network, and save the best checkpoint to `models/`, run:

```bash
uv run well_lstm_pipeline.py
```

This will output the validation loss for each epoch and save `well_lstm_model.pth`, `scaler_x.pkl`, and `scaler_y.pkl` inside the `models/` folder.

### Step 2: Run Predictions (Inference Only)
Once a model is trained and saved, you can perform predictions on the test wells without retraining. To load the saved checkpoint and evaluate on the test set, run:

```bash
uv run well_lstm_predict.py
```

This script outputs the evaluation metrics (**Pearson R**, **R²**, **MAE**, and **RMSE**) for each test well.
