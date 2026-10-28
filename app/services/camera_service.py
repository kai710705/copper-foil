"""管理單一主機鏡頭；不在匯入或讀取狀態時開啟硬體。"""
import threading
import time
import os


class CameraError(Exception):
    pass


class CameraBusyError(CameraError):
    """鏡頭目前由其他使用者控制。"""


class CameraService:
    def __init__(self, index=0, capture_factory=None):
        self.index = index
        self.capture_factory = capture_factory
        self.condition = threading.Condition(threading.RLock())
        self.owner = None
        self.state = 'stopped'
        self.message = '鏡頭尚未啟動'
        self.frame = None
        self.frames = 0
        self.last_seen = 0
        self.stop_event = threading.Event()
        self.thread = None

    def status(self, owner):
        with self.condition:
            if self.owner == owner:
                self.last_seen = time.monotonic()
            return {'state': self.state, 'message': self.message, 'camera_index': self.index,
                    'frames': self.frames, 'can_control': self.owner in (None, owner)}

    def start(self, owner):
        with self.condition:
            if self.owner not in (None, owner):
                raise CameraBusyError('鏡頭正在由另一位使用者操作')
            if self.thread and self.thread.is_alive():
                return self.status(owner)
            self.owner = owner
            self.state = 'starting'
            self.message = '正在開啟鏡頭'
            self.frame = None
            self.frames = 0
            self.last_seen = time.monotonic()
            self.stop_event = threading.Event()
            self.thread = threading.Thread(target=self._capture, daemon=True)
            self.thread.start()
            return self.status(owner)

    def _capture(self):
        capture = None
        try:
            import cv2
            capture = (self.capture_factory(self.index) if self.capture_factory else
                       cv2.VideoCapture(self.index, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY))
            if not capture.isOpened():
                raise CameraError('無法開啟鏡頭，請確認連接、權限與鏡頭是否被其他程式占用')
            while not self.stop_event.is_set():
                if time.monotonic() - self.last_seen > 20:
                    break
                valid, image = capture.read()
                if not valid:
                    raise CameraError('鏡頭影像讀取失敗，請檢查連接後重新啟動')
                valid, encoded = cv2.imencode('.jpg', image)
                if not valid:
                    raise CameraError('影像編碼失敗')
                with self.condition:
                    self.frame = encoded.tobytes()
                    self.frames += 1
                    self.state = 'streaming'
                    self.message = '鏡頭已連接，影像串流中'
                    self.condition.notify_all()
                self.stop_event.wait(0.05)
        except Exception as exc:
            with self.condition:
                self.state = 'error'
                self.message = str(exc) if isinstance(exc, CameraError) else '鏡頭服務無法執行，請確認 OpenCV 安裝與鏡頭設備'
        finally:
            if capture is not None:
                capture.release()
            with self.condition:
                if self.state != 'error':
                    self.state = 'stopped'
                    self.message = '鏡頭已停止並釋放'
                self.frame = None
                self.owner = None
                self.condition.notify_all()

    def stop(self, owner):
        with self.condition:
            if self.owner not in (None, owner):
                raise CameraError('無權停止其他使用者的鏡頭')
            self.stop_event.set()
            thread = self.thread
        if thread:
            thread.join(timeout=3)
        return self.status(owner)

    def latest_frame(self, owner):
        with self.condition:
            if self.owner != owner or self.state not in ('starting', 'streaming') or not self.frame:
                raise CameraError('目前沒有可供辨識的影像')
            self.last_seen = time.monotonic()
            return self.frame

    def stream(self, owner):
        while True:
            with self.condition:
                self.condition.wait(timeout=0.1)
                if self.owner != owner or self.state not in ('starting', 'streaming'):
                    return
                self.last_seen = time.monotonic()
                frame = self.frame
            if frame:
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
