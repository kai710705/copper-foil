"""短暫測試實體鏡頭，完成後一定停止串流並釋放。"""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.camera_service import CameraService
camera=CameraService()
try:
    camera.start(1)
    for _ in range(100):
        state=camera.status(1)
        if state['state'] in ('streaming','error'):break
        time.sleep(.1)
    print(state)
finally:
    print(camera.stop(1))
