import cv2
import time
import requests
import threading
from queue import Queue
from ultralytics import YOLO
from datetime import datetime, timezone

# --- 設定區 ---
RTSP_URL = 0                   # 0 = 本機 webcam，換成 'rtsp://...' 就是網路攝影機
API_URL = 'http://localhost:3001/api/detections'
MODEL_PATH = 'yolov8n.pt'      # 放在 aiot_safety/ 根目錄下即可
CONFIDENCE_THRESHOLD = 0.5
DEVICE_ID = 'pc-webcam-01'


class FrameProducer(threading.Thread):
    """生產者：持續讀取影像幀，放入 Queue（只保留最新一幀避免延遲）"""
    def __init__(self, queue: Queue, source):
        super().__init__(daemon=True)
        self.queue = queue
        self.cap = cv2.VideoCapture(source)

    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Exception:
                    pass
            self.queue.put(frame)
            time.sleep(0.01)
        self.cap.release()
        self.queue.put(None)  # 結束信號


class InferenceConsumer(threading.Thread):
    """消費者：從 Queue 取幀，執行 YOLO 推論並 POST 結果至 Node.js"""
    def __init__(self, queue: Queue):
        super().__init__(daemon=True)
        self.queue = queue
        self.model = YOLO(MODEL_PATH)

    def run(self):
        while True:
            frame = self.queue.get()
            if frame is None:
                break

            results = self.model(frame, verbose=False)

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < CONFIDENCE_THRESHOLD:
                        continue

                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]

                    payload = {
                        "className": class_name,
                        "confidence": round(conf, 4),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "deviceId": DEVICE_ID,
                    }

                    try:
                        requests.post(API_URL, json=payload, timeout=2)
                        print(f"[送出] {class_name} ({conf:.2f})")
                    except requests.exceptions.RequestException as e:
                        print(f"[API 失敗] {e}")


if __name__ == "__main__":
    frame_queue = Queue(maxsize=1)

    producer = FrameProducer(frame_queue, RTSP_URL)
    consumer = InferenceConsumer(frame_queue)

    producer.start()
    consumer.start()

    try:
        producer.join()
        consumer.join()
    except KeyboardInterrupt:
        print("\n[系統終止]")
