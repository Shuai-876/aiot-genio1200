#!/bin/bash
# ============================================================
# download_models.sh
# 在 Genio 1200 上執行，從 GitHub 下載 ONNX 模型
# 使用方式：
#   chmod +x download_models.sh
#   ./download_models.sh
# ============================================================

# ⚠️ 請替換為你的 GitHub 用戶名和 repo 名稱
GITHUB_USER="Shuai-876"
REPO_NAME="aiot-genio1200"
BRANCH="main"

MODEL_DIR="/home/root/models"
MODEL_FILE="last_173epoch.onnx"
DOWNLOAD_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}/raw/${BRANCH}/models/onnx/${MODEL_FILE}"

echo "======================================"
echo " Genio 1200 模型下載腳本"
echo "======================================"

# 建立目錄
mkdir -p "${MODEL_DIR}"

# 確認網路連線
echo "檢查網路連線..."
if ! ping -c 1 github.com &>/dev/null; then
    echo "❌ 無法連線到 GitHub，請確認網路設定"
    exit 1
fi
echo "✅ 網路正常"

# 下載模型
echo ""
echo "下載模型: ${MODEL_FILE}"
echo "來源: ${DOWNLOAD_URL}"
echo ""

wget --show-progress \
     --output-document="${MODEL_DIR}/${MODEL_FILE}" \
     "${DOWNLOAD_URL}"

if [ $? -ne 0 ]; then
    echo "❌ 下載失敗！請確認 GitHub repo 設定正確"
    exit 1
fi

# 確認文件
FILE_SIZE=$(du -h "${MODEL_DIR}/${MODEL_FILE}" | cut -f1)
echo ""
echo "======================================"
echo "✅ 下載成功！"
echo "   路徑：${MODEL_DIR}/${MODEL_FILE}"
echo "   大小：${FILE_SIZE}"
echo "======================================"
echo ""
echo "下一步：執行推理測試"
echo "  python3 /home/root/inference/test_onnx.py"
