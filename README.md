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

### 2. 安装前端依赖

进入 `frontend` 目录后执行：

```bash
npm install
```

## 启动方式

### 1. 启动后端

为了确保后端服务使用正确的虚拟环境运行，避免依赖版本冲突，推荐使用以下两种方式之一启动后端：

#### 方式 A：使用 `uv run`（推荐）
在项目根目录直接运行：
```bash
uv run backend/app.py
```

#### 方式 B：手动激活虚拟环境运行
在项目根目录运行：
```bash
source .venv/bin/activate
python backend/app.py
```

默认地址：

```text
http://127.0.0.1:8000
```

### 2. 启动前端

在 `frontend` 目录执行：

```bash
npm run dev
```

默认地址：

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

该脚本用于读取已训练模型并输出评估结果。

## 后端接口

- `GET /api/health`
- `GET /api/summary`
- `GET /api/wells`
- `POST /api/wells`
- `PUT /api/wells/{well_id}`
- `DELETE /api/wells/{well_id}`
- `GET /api/wells/{well_id}/imports`
- `POST /api/wells/{well_id}/imports`
- `POST /api/wells/{well_id}/predict`
- `GET /api/predictions`
- `GET /api/predictions/{prediction_id}`

## 使用流程

1. 在“钻井管理”里新增钻井。
2. 给钻井上传 CSV 文件。
3. 点击“预测”生成结果。
4. 切换到“钻井预测”查看 ECharts 大屏图表。

## 常见问题

### 1. 预测报模型文件不存在

确认 `models/` 目录下是否存在：

- `well_lstm_model.pth`
- `scaler_x.pkl`
- `scaler_y.pkl`

如果没有，就先跑一遍训练脚本。

### 2. 前端请求失败

确认：

- 后端是否在 `127.0.0.1:8000`
- 前端是否通过 `npm run dev` 启动
- 浏览器请求是否走 `/api` 代理