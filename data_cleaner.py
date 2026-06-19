import pandas as pd
import numpy as np
import pickle
import os
import glob
from sklearn.preprocessing import MinMaxScaler


TRAIN_PATH = "data/train"
TIME_STEPS = 30

def load_and_clean_well(file_path:str) -> pd.DataFrame:
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

def create_sequences(features, labels, time_steps):
    """
    在单口井内创建滑动窗口数据
    """
    X_seq, y_seq = [], []
    for i in range(len(features) - time_steps):
        X_seq.append(features[i : i + time_steps])
        # 预测任务：这里假设是预测当前窗口最后一个点的 CNL 值
        # 如果是 Seq-to-Seq（全序列预测），则改为 labels[i : i + time_steps]
        y_seq.append(labels[i + time_steps]) 
    return np.array(X_seq), np.array(y_seq)

if __name__ == "__main__":
    csv_files = glob.glob(os.path.join(TRAIN_PATH, '*.csv'))
    print(f"找到 {len(csv_files)} 口训练井")

    all_raw_features = []
    all_raw_labels = []
    well_data_list = []

    for file in csv_files:
        df = load_and_clean_well(file)
        if len(df) < (TIME_STEPS + 10): # 长度太短的井直接跳过
            continue
        
        # 准备特征和标签
        f_matrix = df[['AC', 'DEN', 'GR', 'RT', 'RXO']].values
        l_matrix = df[['CNL']].values
        
        # 对非线性特征取对数
        f_matrix[:, [2, 3, 4]] = np.log10(np.maximum(f_matrix[:, [2, 3, 4]], 1e-9))
        
        all_raw_features.append(f_matrix) # [[],[],[]...]
        all_raw_labels.append(l_matrix) # [[y],[y],[y]...]
        well_data_list.append((f_matrix, l_matrix)) # [[[x],[y]],[[x],[y]],[[x],[y]]...]

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    scaler_x.fit(np.vstack(all_raw_features))
    scaler_y.fit(np.vstack(all_raw_labels))

    X_lstm_list = []
    y_lstm_list = []

    for f_matrix, l_matrix in well_data_list:
        # 分别对单口井的数据进行 transform
        f_scaled = scaler_x.transform(f_matrix)
        l_scaled = scaler_y.transform(l_matrix)
        
        # 【关键修改 2】在井内滑动切分窗口
        X_w, y_w = create_sequences(f_scaled, l_scaled, TIME_STEPS)
        
        if len(X_w) > 0:
            X_lstm_list.append(X_w)
            y_lstm_list.append(y_w)

    # 第三步：拼接所有井生成的序列
    X_final = np.vstack(X_lstm_list)
    y_final = np.vstack(y_lstm_list)

    print(f"最终输出矩阵形状:")
    print(f"X_train_lstm shape: {X_final.shape}")  # 应该是 (总样本数, TIME_STEPS, 5)
    print(f"y_train_lstm shape: {y_final.shape}")  # 应该是 (总样本数, 1)

    # 保存文件
    with open('scaler_x.pkl', 'wb') as f:
        pickle.dump(scaler_x, f)
    with open('scaler_y.pkl', 'wb') as f:
        pickle.dump(scaler_y, f)
            
    np.save('X_train_lstm.npy', X_final)
    np.save('y_train_lstm.npy', y_final)
    print("清洗与时序转换完成！")