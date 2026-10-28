import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.repositories.database import get_db

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.path=str(Path(self.tmp.name)/'safety.sqlite')
        self.app=create_app({'TESTING':True,'DATABASE':self.path})
        self.client=self.app.test_client()
        self.call('post','/api/v1/auth/login',{'username':'admin','password':'admin@123'})
        self.call('post','/api/v1/auth/password',{'current_password':'admin@123','password':'safePassword123'})
    def tearDown(self):self.tmp.cleanup()
    def call(self,method,path,data):
        token=self.client.get('/api/v1/auth/csrf').json['data']['csrf_token']
        return getattr(self.client,method)(path,json=data,headers={'X-CSRF-Token':token})
    def test_resources_and_history_preservation(self):
        page=self.client.get('/admin').get_data(as_text=True)
        for label in ('實驗室資源','攝影機資源','標示已處理'):
            self.assertIn(label,page)
        lab=self.call('post','/api/v1/admin/laboratories',{'name':'新增實驗室','location':'3F'})
        self.assertEqual(lab.status_code,201);lid=lab.json['data']['id']
        camera=self.call('post','/api/v1/admin/cameras',{'name':'CAM','laboratory_id':lid})
        self.assertEqual(camera.status_code,201);cid=camera.json['data']['id']
        self.assertEqual(self.call('post','/api/v1/admin/cameras',{'name':'bad','laboratory_id':999}).status_code,404)
        self.assertEqual(self.call('patch',f'/api/v1/admin/cameras/{cid}',{'device_index':-1}).status_code,400)
        with self.app.app_context():
            with get_db():get_db().execute("INSERT INTO safety_alerts(title,area,alert_type,laboratory_id) VALUES('保留事件','3F','測試',?)",(lid,))
        self.assertEqual(self.call('patch',f'/api/v1/admin/laboratories/{lid}',{'active':0}).status_code,200)
        self.assertNotIn(cid,[r['id'] for r in self.client.get('/api/v1/cameras').json['data']])
        self.assertEqual(self.call('patch',f'/api/v1/admin/cameras/{cid}',{'active':0}).status_code,200)
        with self.app.app_context():self.assertEqual(get_db().execute('SELECT COUNT(*) FROM safety_alerts WHERE laboratory_id=?',(lid,)).fetchone()[0],1)
        create_app({'TESTING':True,'DATABASE':self.path})
        self.assertEqual(self.client.get('/api/v1/admin/cameras').json['data'][0]['active'],0)
    def test_alerts_and_statistics(self):
        public=self.app.test_client()
        self.assertEqual(public.get('/api/v1/monitoring').status_code,401)
        initial=self.client.get('/api/v1/monitoring').json['data']
        aid=initial['alerts'][0]['id']
        self.assertEqual(self.call('patch',f'/api/v1/admin/alerts/{aid}',{'status':'invalid'}).status_code,400)
        self.assertEqual(self.call('patch','/api/v1/admin/alerts/999',{'status':'resolved'}).status_code,404)
        self.assertEqual(self.call('patch',f'/api/v1/admin/alerts/{aid}',{'status':'resolved'}).status_code,200)
        updated=self.client.get('/api/v1/admin/dashboard').json['data']
        self.assertEqual(updated['stats']['alerts'],initial['stats']['alerts']-1)
        self.assertTrue(updated['stats']['safe_rate_demo'])
        create_app({'TESTING':True,'DATABASE':self.path})
        self.assertEqual(self.client.get('/api/v1/monitoring').json['data']['stats']['alerts'],initial['stats']['alerts']-1)
    def test_audit_create_complete_and_persistence(self):
        page=self.client.get('/admin').get_data(as_text=True)
        for label in ('稽核紀錄','區域','稽核人員','改善期限','新增稽核紀錄','標記改善完成'):
            self.assertIn(label,page)
        initial=self.client.get('/api/v1/monitoring').json['data']['stats']['audits']
        data={'area':'材料區','inspector':'稽核人員','issue':'改善標示','due_date':'2026-11-10'}
        self.assertEqual(self.call('post','/api/v1/admin/audits',{**data,'due_date':'2026-02-30'}).status_code,400)
        self.assertEqual(self.call('post','/api/v1/admin/audits',{**data,'issue':''}).status_code,400)
        created=self.call('post','/api/v1/admin/audits',data)
        self.assertEqual(created.status_code,201);aid=created.json['data']['id']
        self.assertEqual(self.client.get('/api/v1/monitoring').json['data']['stats']['audits'],initial+1)
        self.assertEqual(self.call('patch','/api/v1/admin/audits/999',{'status':'completed'}).status_code,404)
        self.assertEqual(self.call('patch',f'/api/v1/admin/audits/{aid}',{'status':'invalid'}).status_code,400)
        self.assertEqual(self.call('patch',f'/api/v1/admin/audits/{aid}',{'status':'completed'}).status_code,200)
        create_app({'TESTING':True,'DATABASE':self.path})
        snapshot=self.client.get('/api/v1/monitoring').json['data']
        self.assertEqual(snapshot['stats']['audits'],initial)
        self.assertEqual(next(r for r in snapshot['audits'] if r['id']==aid)['status'],'completed')
        self.call('post','/api/v1/auth/register',{'username':'normal','email':'normal@example.com','password':'password123'})
        with self.app.app_context():
            with get_db():get_db().execute("UPDATE users SET approval_status='approved' WHERE username='normal'")
        self.call('post','/api/v1/auth/login',{'username':'normal','password':'password123'})
        self.assertEqual(self.call('post','/api/v1/admin/audits',data).status_code,403)
        self.assertEqual(self.call('patch',f'/api/v1/admin/audits/{aid}',{'status':'completed'}).status_code,403)

if __name__=='__main__':unittest.main()
