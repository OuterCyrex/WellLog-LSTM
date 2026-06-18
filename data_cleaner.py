import pandas as pd
import numpy as np
import pickle
import os
import glob
from sklearn.preprocessing import MinMaxScaler


TRAIN_PATH = r"E:\Adownloads\WellLog-LSTM\data\train"


def load_and_clean_well(file_path):
    df = pd.read_csv(file_path, skiprows=[1])
    df.columns = ['Well', 'Dataset', 'Depth', 'AC', 'CAL', 'CNL', 'DEN', 'GR', 'RT', 'RXO']
    df.replace(-9999, np.nan, inplace=True)

    bounds = {
        'AC': (33, 180), 'CAL': (0, 100), 'CNL': (-5, 50),
        'DEN': (1.5, 3.01), 'GR': (3, 500), 'RT': (1, 10000), 'RXO': (1, 10000)
    }
    for col, (low, high) in bounds.items():
        if col in df.columns:
            df[col] = df[col].clip(lower=low, upper=high)

    curve_cols = ['AC', 'CAL', 'CNL', 'DEN', 'GR', 'RT', 'RXO']
    df[curve_cols] = df[curve_cols].interpolate(method='linear', limit_direction='both')
    df[curve_cols] = df[curve_cols].fillna(method='ffill').fillna(method='bfill')
    df.dropna(subset=curve_cols, inplace=True)
    return df


if __name__ == "__main__":
    all_features = []
    all_labels = []
    csv_files = glob.glob(os.path.join(TRAIN_PATH, '*.csv'))
    print(f"找到 {len(csv_files)} 口训练井")

    for file in csv_files:
        df = load_and_clean_well(file)
        if len(df) < 10:
            continue
        feature = df[['AC', 'DEN', 'GR', 'RT', 'RXO']].values
        label = df[['CNL']].values
        # 对 GR, RT, RXO 取对数
        feature[:, [2, 3, 4]] = np.log10(np.maximum(feature[:, [2, 3, 4]], 1e-9))
        all_features.append(feature)
        all_labels.append(label)

    X = np.vstack(all_features)
    y = np.vstack(all_labels)

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_scaled = scaler_x.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y)

    # 保存清洗后的数据和缩放器
    with open('scaler_x.pkl', 'wb') as f:
        pickle.dump(scaler_x, f)
    with open('scaler_y.pkl', 'wb') as f:
        pickle.dump(scaler_y, f)
    np.save('X_train_clean.npy', X_scaled)
    np.save('y_train_clean.npy', y_scaled)
    print("清洗完成！生成了 X_train_clean.npy, y_train_clean.npy 和两个 scaler 文件")