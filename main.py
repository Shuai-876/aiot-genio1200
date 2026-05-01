import cv2
import time
import requests
import threading
import webbrowser
from queue import Queue
from flask import Flask, Response
from ultralytics import YOLO
from datetime import datetime, timezone

# --- 設定區 ---
RTSP_URL = 'rtsp://admin:sp77343488@@192.168.50.45:554'
API_URL = 'http://localhost:3001/api/detections'
MODEL_PATH = r'C:\test\aiot_genio1200\aiot\runs\detect\genio_training\yolov8n_construction\weights\best.pt'
CONFIDENCE_THRESHOLD = 0.5
DEVICE_ID = 'pc-webcam-01'

# 全域 frame buffer（thread-safe 用 lock）
latest_frame = None
frame_lock = threading.Lock()

app = Flask(__name__)


class FrameProducer(threading.Thread):
    """生產者：持續讀取影像幀，放入 Queue（只保留最新一幀避免延遲）"""
    def __init__(self, queue: Queue, source):
        super().__init__(daemon=True)
        self.queue = queue
        self.cap = cv2.VideoCapture(source)
        # 減少 RTSP 內部緩衝，降低延遲
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def run(self):
        print(f"[Producer] 嘗試連線至: {RTSP_URL}")
        if not self.cap.isOpened():
            print("[Producer] ❌ 無法開啟影片來源！")
            self.queue.put(None)
            return

        print("[Producer] ✅ 影片來源已開啟，開始讀取幀...")
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("[Producer] ⚠️ 讀取幀失敗 (End of stream or error)")
                break
            if not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Exception:
                    pass
            self.queue.put(frame)
        self.cap.release()
        print("[Producer] 停止讀取")
        self.queue.put(None)


# 每個類別固定顏色（BGR）
COLOR_PALETTE = [
    (0, 212, 255), (0, 255, 136), (255, 184, 0), (168, 85, 247),
    (255, 71, 87),  (62, 207, 142),(249, 115, 22),(6, 182, 212),
    (236, 72, 153),(132, 204, 22),
]

def get_color(class_id: int):
    return COLOR_PALETTE[class_id % len(COLOR_PALETTE)]


class InferenceConsumer(threading.Thread):
    """消費者：從 Queue 取幀，執行 YOLO 推論，更新全域 buffer"""
    def __init__(self, queue: Queue):
        super().__init__(daemon=True)
        self.queue = queue
        self.model = YOLO(MODEL_PATH)

    def run(self):
        global latest_frame
        last_send_time = time.time()
        # 用於暫存一秒內的統計結果
        stats_buffer = {} 

        print("--- [Consumer] 偵測執行緒啟動成功 ---", flush=True)
        while True:
            # print("[Consumer] 等待 Queue 中的幀...", end='\r', flush=True)
            frame = self.queue.get()
            if frame is None:
                print("[Consumer] 收到 None，停止偵測迴圈", flush=True)
                break
            
            # print(".", end="", flush=True) # 每一幀印一個點表示活著
            results = self.model(frame, verbose=False)
            annotated = frame.copy()
            
            # 每張 frame 的暫時統計
            current_frame_detections = []

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < CONFIDENCE_THRESHOLD:
                        continue

                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    color = get_color(class_id)
                    
                    current_frame_detections.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": conf
                    })

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(annotated, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # 每秒發送一次彙整資料
            if time.time() - last_send_time >= 1.0:
                summary = {}
                for d in current_frame_detections:
                    cid = d["class_id"]
                    summary[cid] = summary.get(cid, 0) + 1

                print(f"\n[Consumer] {datetime.now().strftime('%H:%M:%S')} | {summary}", flush=True)

                payload = {
                    "summary": summary,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "deviceId": DEVICE_ID,
                    "isSummary": True
                }

                try:
                    requests.post(API_URL, json=payload, timeout=0.5)
                except:
                    print("!", end="", flush=True)

                last_send_time = time.time()

            # 更新全域 buffer
            _, jpeg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
            with frame_lock:
                latest_frame = jpeg.tobytes()


def generate():
    """MJPEG stream generator"""
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.02)
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
  <title>AIoT Safety Monitor</title>
  <style>
    body { margin: 0; background: #111; display: flex; justify-content: center; align-items: center; height: 100vh; }
    img { max-width: 100%; border: 2px solid #00d4ff; border-radius: 4px; }
  </style>
</head>
<body>
  <img src="/video_feed" />
</body>
</html>'''


if __name__ == "__main__":
    frame_queue = Queue(maxsize=1)

    producer = FrameProducer(frame_queue, RTSP_URL)
    consumer = InferenceConsumer(frame_queue)

    producer.start()
    consumer.start()

    # 等 Flask 起來後自動開瀏覽器
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()

    print("[Flask] http://localhost:5000 開啟瀏覽器看串流")
    app.run(host='0.0.0.0', port=5000, use_reloader=False)
