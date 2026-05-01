# AIoT Genio 1200 - 建設工地安全監測系統

基於 YOLOv8 的即時建設工地安全檢測系統，在 MediaTek Genio 1200 上運行，使用 ONNX 模型格式和 NNStreamer 進行硬件加速。

## 🎯 功能

- **實時物件偵測**：RTSP 攝像頭串流 → YOLOv8 推理
- **6 類別檢測**：安全帽、安全衣、警察、違規人員等
- **資料庫儲存**：PostgreSQL + Node.js Express API
- **可視化儀表板**：Web 前端 + Grafana 監控
- **硬件加速**：MediaTek Genio 1200 NPU/MDLA (規劃中)

## 📁 專案結構

```
aiot-genio1200/
├── main.py                    # 主推理腳本（RTSP 支援）
├── check_db.sql               # 資料庫初始化 SQL
│
├── aiot_safety/
│   ├── backend/               # Node.js Express 後端
│   │   ├── server.js          # API 伺服器 (port 3001)
│   │   ├── config/            # 資料庫配置
│   │   ├── models/            # 資料庫模型 (Sequelize)
│   │   └── package.json       # Node.js 依賴
│   │
│   ├── frontend/              # 前端儀表板
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   │
│   ├── worker/                # Python 推理 worker
│   │   └── main.py
│   │
│   └── grafana/               # Grafana 監控配置
│       └── docker-compose.yml
│
├── models/
│   ├── onnx/
│   │   ├── last_173epoch.onnx  # ⭐ ONNX 量化模型 (10.2 MB)
│   │   └── model_info.txt      # 模型規格
│   └── pytorch/
│       └── yolov8n.pt          # 原始 PyTorch 模型
│
├── inference/
│   └── test_onnx.py            # 模型推理測試腳本
│
└── scripts/
    └── download_models.sh      # Genio 1200 模型下載腳本
```

## 🔧 本地開發

### 1. 環境準備

```bash
# Python 依賴
pip install ultralytics opencv-python onnxruntime numpy

# Node.js 依賴
cd aiot_safety/backend
npm install
```

### 2. 資料庫設定

```bash
# PostgreSQL（假設已安裝）
createdb aiot_safety
psql aiot_safety < check_db.sql

# 或修改 backend/config/database.js 中的憑證
```

### 3. 執行系統

```bash
# 終端 1：啟動 Node.js 後端
cd aiot_safety/backend
npm start
# → API 在 http://localhost:3001

# 終端 2：啟動推理
python main.py
# → 預設使用 webcam，或設定 RTSP URL

# 終端 3：開啟前端
# 打開 aiot_safety/frontend/index.html 在瀏覽器
```

## 🚀 Genio 1200 部署

### 1. 下載模型

```bash
cd /home/root
wget https://raw.githubusercontent.com/Shuai-876/aiot-genio1200/main/scripts/download_models.sh
chmod +x download_models.sh
./download_models.sh
```

### 2. 測試推理

```bash
wget https://raw.githubusercontent.com/Shuai-876/aiot-genio1200/main/inference/test_onnx.py
python3 test_onnx.py
# 預期輸出：平均推理時間、FPS
```

### 3. 完整系統部署

在 Genio 1200 上：
```bash
# 複製後端代碼
git clone https://github.com/Shuai-876/aiot-genio1200.git
cd aiot-genio1200

# 安裝依賴
pip3 install onnxruntime numpy opencv-python
cd aiot_safety/backend && npm install

# 配置資料庫（PostgreSQL 或其他）
# 修改 backend/config/database.js

# 啟動推理系統
python3 main.py --source rtsp://camera-ip:554/stream

# 啟動後端 API
cd aiot_safety/backend && npm start
```

## 📊 模型信息

| 項目 | 值 |
|------|-----|
| 框架 | YOLOv8n |
| 格式 | ONNX (opset 19) |
| 訓練輪數 | 173 epochs |
| 模型大小 | 10.2 MB |
| 輸入 | [1, 3, 640, 640] (RGB, 0-1) |
| 輸出 | [1, 10, 8400] (bbox + 6 classes) |
| 推理延遲（PC CPU）| ~54 ms / 18 FPS |

## 🎓 類別對應

- `0`: people with helmet (pwh) - 戴安全帽的人
- `1`: people with vest (pwv) - 穿安全衣的人
- `2`: people no helmet (pnh) - 未戴安全帽的人
- `3`: people no vest (pnv) - 未穿安全衣的人
- `4`: police - 警察
- `5`: people with vest new (pwv1) - 新型安全衣

## 🔌 API 端點 (Node.js Express)

### 偵測結果
```
POST /api/detections
{
  "className": "people with helmet",
  "confidence": 0.95,
  "timestamp": "2026-05-01T12:34:56Z",
  "deviceId": "genio-1200-01"
}

GET /api/detections?limit=100
```

### 系統健康檢查
```
GET /health
```

## 📈 效能指標

**在 Genio 1200 上的預期效能：**
- ONNX Runtime (CPU): 30-50 FPS
- NNStreamer + Neuron SDK (NPU): 100-200+ FPS

## 🛠️ 疑難排除

### 1. 模型推理失敗
```bash
# 檢查 onnxruntime 是否安裝
python3 -c "import onnxruntime; print(onnxruntime.__version__)"

# 如未安裝
pip3 install onnxruntime
```

### 2. PostgreSQL 連線錯誤
```bash
# 修改 backend/config/database.js
# 確認資料庫伺服器、用戶名、密碼設定正確
```

### 3. RTSP 串流連線失敗
```bash
# 確認攝像頭 IP 和連接埠
# 測試連通性
ping <camera-ip>
```

## 📝 環境變數 (.env)

```bash
# 資料庫
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aiot_safety
DB_USER=postgres
DB_PASSWORD=your_password

# API
API_PORT=3001

# 推理
CONFIDENCE_THRESHOLD=0.35
RTSP_URL=rtsp://camera-ip:554/stream
```

## 🔐 安全提示

⚠️ **不要**將以下文件提交到 GitHub：
- `.env`（含資料庫密碼）
- `node_modules/`
- `.vscode/`
- 私人的 RTSP URL

## 📚 相關資源

- [YOLOv8 文檔](https://docs.ultralytics.com)
- [MediaTek Genio 1200](https://mediatek.gitlab.io/genio/doc/iot-aihub)
- [NNStreamer](https://mediatek.gitlab.io/genio/doc/iot-aihub/master/ai_hub/supported_os/yocto/litert/nnstreamer.html)
- [ONNX Runtime](https://onnxruntime.ai)

## 👤 作者

AIoT 團隊  
建設工地安全監測專案

## 📄 授權

MIT License

---

**最後更新：2026-05-01**
