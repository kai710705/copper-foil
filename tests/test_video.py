"""以可控制的擷取設備驗證生命週期，不假設測試機有實體 CAM。"""
import sys, unittest, tempfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.camera_service import CameraBusyError, CameraService

class VideoTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.app=create_app({'TESTING':True,'DATABASE':str(Path(self.directory.name)/'test.sqlite')})
        self.client=self.app.test_client()
    def tearDown(self):
        self.directory.cleanup()
    def test_auth_and_csrf(self):
        self.assertEqual(self.client.get('/api/v1/camera/status').status_code,401)
        token=self.client.get('/api/v1/auth/csrf').json['data']['csrf_token']
        self.client.post('/login',data={'username':'admin','password':'admin@123','csrf_token':token})
        token=self.client.get('/api/v1/auth/csrf').json['data']['csrf_token']
        self.client.post('/api/v1/auth/password',json={'current_password':'admin@123','password':'safePassword123'},headers={'X-CSRF-Token':token})
        self.assertEqual(self.client.get('/video').status_code,200)
        self.assertEqual(self.client.post('/api/v1/camera/start').status_code,403)
        self.assertEqual(self.client.get('/api/v1/camera/stream').status_code,409)
    def test_capture_lifecycle(self):
        import numpy as np
        class Fake:
            released=False
            def isOpened(self):return True
            def read(self):return True,np.zeros((48,64,3),dtype=np.uint8)
            def release(self):self.released=True
        fake=Fake(); opened=[]
        def factory(index):opened.append(index);return fake
        camera=CameraService(capture_factory=factory)
        self.assertEqual(camera.status(1)['state'],'stopped');self.assertEqual(opened,[])
        camera.start(1)
        for _ in range(100):
            if camera.status(1)['state']=='streaming':break
            time.sleep(.02)
        self.assertEqual(camera.status(1)['state'],'streaming')
        stream=camera.stream(1);part=next(stream)
        self.assertIn(b'Content-Type: image/jpeg',part);self.assertIn(b'\xff\xd8',part)
        stream.close();camera.stop(1)
        self.assertTrue(fake.released);self.assertEqual(camera.status(1)['state'],'stopped')
    def test_device_failure(self):
        class Missing:
            def isOpened(self):return False
            def release(self):pass
        camera=CameraService(capture_factory=lambda _:Missing());camera.start(1)
        camera.thread.join(5)
        self.assertEqual(camera.status(1)['state'],'error')

    def test_other_owner_is_busy(self):
        camera=CameraService()
        camera.owner=1
        camera.last_seen=time.monotonic()
        with self.assertRaises(CameraBusyError):
            camera.start(2)

if __name__=='__main__':unittest.main()
