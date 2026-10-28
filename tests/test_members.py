import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.repositories.database import get_db

class MemberTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.app=create_app({'TESTING':True,'DATABASE':str(Path(self.tmp.name)/'test.sqlite')})
        self.client=self.app.test_client()
    def token(self,client=None):
        return (client or self.client).get('/api/v1/auth/csrf').json['data']['csrf_token']
    def post(self,path,data,client=None):
        client=client or self.client
        return client.post(path,json=data,headers={'X-CSRF-Token':self.token(client)})
    def tearDown(self):self.tmp.cleanup()
    def register(self,**changes):
        data={'username':'newmember','email':'new@example.com','password':'password123','role':'user'}
        data.update(changes)
        return self.post('/api/v1/auth/register',data)
    def test_register_validation_and_role(self):
        self.assertEqual(self.register(role='owner').status_code,400)
        self.assertEqual(self.register(email='invalid').status_code,400)
        self.assertEqual(self.register(password='short').status_code,400)
        self.assertEqual(self.post('/api/v1/auth/register',{}).status_code,400)
        self.assertEqual(self.register(role='admin').status_code,201)
        self.assertEqual(self.register().status_code,409)
        with self.app.app_context():
            row=get_db().execute("SELECT * FROM users WHERE username='newmember'").fetchone()
            self.assertEqual(row['approval_status'],'pending')
            self.assertNotEqual(row['password_hash'],'password123')
        self.assertEqual(self.client.post('/register',data={'username':'x','csrf_token':self.token()}).status_code,400)
    def test_login_password_change_and_logout(self):
        self.assertEqual(self.register().status_code,201)
        self.assertEqual(self.post('/api/v1/auth/login',{'username':'newmember','password':'password123'}).status_code,401)
        login=self.post('/api/v1/auth/login',{'username':'admin','password':'admin@123'})
        self.assertEqual(login.status_code,200)
        self.assertEqual(login.json['data']['redirect'],'/password')
        self.assertNotIn('password_hash',login.json['data']['user'])
        self.assertEqual(self.client.get('/api/v1/admin/users').status_code,403)
        self.assertEqual(self.post('/api/v1/auth/password',{'current_password':'wrong','password':'safePassword123'}).status_code,400)
        self.assertEqual(self.post('/api/v1/auth/password',{'current_password':'admin@123','password':'safePassword123'}).status_code,200)
        self.assertEqual(self.client.get('/api/v1/admin/users').status_code,200)
        self.assertEqual(self.post('/api/v1/auth/logout',{}).status_code,200)
        self.assertEqual(self.post('/api/v1/auth/login',{'username':'admin','password':'admin@123'}).status_code,401)
        self.assertEqual(self.post('/api/v1/auth/login',{'username':'admin','password':'safePassword123'}).status_code,200)
    def test_authorization_and_csrf(self):
        self.assertEqual(self.client.get('/api/v1/monitoring').status_code,401)
        self.assertEqual(self.client.post('/api/v1/auth/login',json={'username':'admin','password':'admin@123'}).status_code,403)
        self.register()
        with self.app.app_context():
            with get_db():get_db().execute("UPDATE users SET approval_status='approved' WHERE username='newmember'")
        self.assertEqual(self.post('/api/v1/auth/login',{'username':'newmember','password':'password123'}).status_code,200)
        self.assertEqual(self.client.get('/api/v1/admin/users').status_code,403)
        self.assertEqual(self.client.get('/video').status_code,200)
        with self.app.app_context():
            with get_db():get_db().execute("UPDATE users SET approval_status='disabled' WHERE username='newmember'")
        self.assertEqual(self.client.get('/api/v1/monitoring').status_code,401)
        self.assertEqual(self.client.get('/api/v1/camera/status').status_code,401)
    def admin_login(self):
        self.post('/api/v1/auth/login',{'username':'admin','password':'admin@123'})
        self.post('/api/v1/auth/password',{'current_password':'admin@123','password':'safePassword123'})
    def test_review_transaction_and_protection(self):
        from app.services.member_service import MemberService
        from app.services.errors import DomainError
        self.register();self.admin_login()
        with self.app.app_context():
            uid=get_db().execute("SELECT id FROM users WHERE username='newmember'").fetchone()[0]
            MemberService.review(1,uid,'approved')
            history=MemberService.history(1,uid)
            self.assertEqual(history[0]['actor_id'],1)
            self.assertEqual(history[0]['from_status'],'pending')
            self.assertTrue(history[0]['created_at'])
            with self.assertRaises(DomainError):MemberService.review(1,1,'disabled')
            with self.assertRaises(DomainError):MemberService.review(1,999,'approved')
            get_db().execute("CREATE TRIGGER fail_history BEFORE INSERT ON member_review_history BEGIN SELECT RAISE(ABORT,'test'); END")
            with self.assertRaises(Exception):MemberService.review(1,uid,'disabled')
            self.assertEqual(get_db().execute('SELECT approval_status FROM users WHERE id=?',(uid,)).fetchone()[0],'approved')
            get_db().execute('DROP TRIGGER fail_history')
            MemberService.review(1,uid,'disabled')
        self.register(username='rejectme',email='reject@example.com')
        with self.app.app_context():
            uid=get_db().execute("SELECT id FROM users WHERE username='rejectme'").fetchone()[0]
            MemberService.review(1,uid,'rejected')
            self.assertEqual(MemberService.history(1,uid)[0]['to_status'],'rejected')
    def test_review_api(self):
        self.register();self.admin_login()
        pending=self.client.get('/api/v1/admin/users?status=pending').json['data']
        page=self.client.get('/admin')
        self.assertEqual(page.status_code,200)
        self.assertIn('/static/js/admin.js',page.get_data(as_text=True))
        self.assertIn('審核歷程',page.get_data(as_text=True))
        uid=pending[0]['id'];headers={'X-CSRF-Token':self.token()}
        self.assertEqual(self.client.patch(f'/api/v1/admin/users/{uid}',json={'approval_status':'approved'},headers=headers).status_code,200)
        history=self.client.get(f'/api/v1/admin/users/{uid}/history')
        self.assertEqual(history.status_code,200)
        self.assertEqual(history.json['data'][0]['actor_name'],'admin')
        self.assertEqual(self.client.patch('/api/v1/admin/users/999',json={'approval_status':'approved'},headers=headers).status_code,404)
        self.assertEqual(self.client.patch(f'/api/v1/admin/users/{uid}',json={'approval_status':'approved'},headers=headers).status_code,409)
        member=self.app.test_client()
        self.post('/api/v1/auth/login',{'username':'newmember','password':'password123'},member)
        self.assertEqual(member.get(f'/api/v1/admin/users/{uid}/history').status_code,403)
        self.assertEqual(member.patch(f'/api/v1/admin/users/{uid}',json={'approval_status':'disabled'},headers={'X-CSRF-Token':self.token(member)}).status_code,403)
        self.client.patch(f'/api/v1/admin/users/{uid}',json={'approval_status':'disabled'},headers=headers)
        self.assertEqual(member.get('/api/v1/monitoring').status_code,401)

if __name__=='__main__':unittest.main()
