"""
test_onnx.py - 在 Genio 1200 上測試 ONNX 模型推理
使用方式：python3 test_onnx.py
"""

import numpy as np
import time
import os
import sys

# 類別名稱（對應你訓練的 6 個類別）
CLASS_NAMES = [
    'people with helmet (pwh)',
    'people with vest (pwv)',
    'people no helmet (pnh)',
    'people no vest (pnv)',
    'police',
    'people with vest new (pwv1)',
]

def load_model(model_path):
    """載入 ONNX 模型"""
    try:
        import onnxruntime as ort
    except ImportError:
        print("❌ 未安裝 onnxruntime，請執行：")
        print("   pip3 install onnxruntime")
        sys.exit(1)

    if not os.path.exists(model_path):
        print(f"❌ 找不到模型：{model_path}")
        print("   請先執行 download_models.sh")
        sys.exit(1)

    # 使用 CPU 執行（Genio 1200 上可換為 NPU 加速）
    providers = ['CPUExecutionProvider']

    print(f"載入模型：{model_path}")
    session = ort.InferenceSession(model_path, providers=providers)

    inp = session.get_inputs()[0]
    out = session.get_outputs()[0]
    file_mb = os.path.getsize(model_path) / 1024 / 1024

    print(f"✅ 模型載入成功")
    print(f"   大小   : {file_mb:.2f} MB")
    print(f"   輸入   : {inp.name} {inp.shape}")
    print(f"   輸出   : {out.name} {out.shape}")

    return session


def benchmark(session, n=20):
    """測試推理速度"""
    inp_name = session.get_inputs()[0].name
    dummy = np.random.rand(1, 3, 640, 640).astype(np.float32)

    # 暖機 3 次
    for _ in range(3):
        session.run(None, {inp_name: dummy})

    # 正式計時
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        session.run(None, {inp_name: dummy})
        times.append(time.perf_counter() - t0)

    avg_ms  = np.mean(times)   * 1000
    min_ms  = np.min(times)    * 1000
    max_ms  = np.max(times)    * 1000
    fps     = 1000 / avg_ms

    print(f"\n⚡ 推理速度（{n} 次平均）")
    print(f"   平均：{avg_ms:.1f} ms   →  {fps:.1f} FPS")
    print(f"   最快：{min_ms:.1f} ms")
    print(f"   最慢：{max_ms:.1f} ms")
    return avg_ms


def postprocess(output, conf_threshold=0.35, iou_threshold=0.45):
    """
    解析 YOLOv8 輸出 [1, 10, 8400]
    回傳：list of (x1, y1, x2, y2, conf, class_id)
    """
    pred = output[0]          # shape: [10, 8400]
    pred = pred.transpose()   # shape: [8400, 10]

    boxes_xywh = pred[:, :4]  # cx, cy, w, h
    scores     = pred[:, 4:]  # 6 個類別分數

    class_ids  = np.argmax(scores, axis=1)
    confs      = np.max(scores, axis=1)

    # 過濾低信心度
    mask = confs > conf_threshold
    boxes_xywh = boxes_xywh[mask]
    confs      = confs[mask]
    class_ids  = class_ids[mask]

    if len(boxes_xywh) == 0:
        return []

    # cx,cy,w,h → x1,y1,x2,y2
    x1 = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    y1 = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    x2 = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    y2 = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2

    detections = []
    for i in range(len(confs)):
        detections.append((
            float(x1[i]), float(y1[i]),
            float(x2[i]), float(y2[i]),
            float(confs[i]), int(class_ids[i])
        ))
    return detections


def test_with_image(session, image_path):
    """用真實圖片測試推理結果"""
    try:
        import cv2
    except ImportError:
        print("⚠️  未安裝 opencv，跳過真實圖片測試")
        return

    if not os.path.exists(image_path):
        print(f"⚠️  圖片不存在：{image_path}")
        return

    inp_name = session.get_inputs()[0].name

    img = cv2.imread(image_path)
    img_resized = cv2.resize(img, (640, 640))
    inp_tensor = img_resized.astype(np.float32) / 255.0
    inp_tensor = np.transpose(inp_tensor, (2, 0, 1))   # HWC → CHW
    inp_tensor = np.expand_dims(inp_tensor, axis=0)     # 加 batch 維度

    output = session.run(None, {inp_name: inp_tensor})
    detections = postprocess(output)

    print(f"\n📷 圖片推理結果：{image_path}")
    if detections:
        for x1, y1, x2, y2, conf, cls in detections:
            print(f"   {CLASS_NAMES[cls]:<35} 信心度: {conf:.2f}")
    else:
        print("   未偵測到目標（conf > 0.35）")


def main():
    model_path = "/home/root/models/last_173epoch.onnx"

    # 允許命令列參數指定路徑
    if len(sys.argv) > 1:
        model_path = sys.argv[1]

    print("=" * 50)
    print(" Genio 1200 ONNX 推理測試")
    print("=" * 50)

    session = load_model(model_path)
    benchmark(session)

    # 如果有提供圖片路徑，用真實圖片測試
    if len(sys.argv) > 2:
        test_with_image(session, sys.argv[2])

    print("\n✅ 測試完成！模型可以正常運行")
    print("   下一步：整合 NNStreamer 管道")


if __name__ == "__main__":
    main()
