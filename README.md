# WellLog-LSTM

这是一个基于 LSTM 的测井曲线重建项目，当前已补充本地管理后台：

- 后端：`FastAPI + SQLAlchemy ORM + SQLite`
- 前端：`Vue3 + Vite + Element Plus + ECharts`
- 模型：沿用现有训练好的 LSTM 推理文件，不改核心模型代码

## 项目功能

- 钻井管理
- CSV 数据导入
- 模型预测
- 预测结果可视化

## 目录说明

```text
WellLog-LSTM/
├─ backend/          # 后端接口、ORM、预测封装
├─ frontend/         # Vue3 前端
├─ data/             # 原始数据和训练数据
├─ models/           # 训练好的模型文件和 scaler
├─ docs/             # 说明文档
├─ well_common.py    # 公共数据清洗和模型定义
├─ well_lstm_pipeline.py  # 训练脚本
└─ well_lstm_predict.py   # 推理脚本
```

## 环境安装

项目建议使用 `uv` 管理 Python 依赖。

### 1. 安装后端依赖

```bash
uv sync
```

如果需要重新训练模型，再安装训练额外依赖：

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
http://127.0.0.1:5173
```

## 数据说明

当前系统使用本地 SQLite 数据库，CSV 文件只保存路径，不把文件内容写入数据库。

- 数据库文件：`backend/storage/welllog.sqlite3`
- 上传文件目录：`backend/storage/uploads/`

## 模型说明

后端推理会读取以下文件：

- `models/well_lstm_model.pth`
- `models/scaler_x.pkl`
- `models/scaler_y.pkl`

如果这三个文件缺失，后端预测接口会提示模型工件不存在。

## 训练与推理

### 训练模型

```bash
uv run well_lstm_pipeline.py
```

训练完成后会输出并保存模型文件到 `models/` 目录。

### 仅做推理

```bash
uv run well_lstm_predict.py
```

This script outputs the evaluation metrics (**Pearson R**, **R²**, **MAE**, and **RMSE**) for each test well.
