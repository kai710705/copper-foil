"""讀取實際 SQLite 結構，產生繁體中文資料結構報告與 PDF。"""
from pathlib import Path
import sys, sqlite3, html, textwrap
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

root = Path(__file__).resolve().parent
app = create_app()
db = sqlite3.connect(app.config['DATABASE'])
db.row_factory = sqlite3.Row
tables = ['users','rooms','bookings','safety_alerts','audits','member_review_history','laboratories','cameras','schema_migrations']
names = {'users':'會員帳號','rooms':'會議廳資源（舊系統保留）','bookings':'行事曆預約（舊系統保留）','safety_alerts':'工安警示','audits':'稽核紀錄'}
meaning = {'id':'資料唯一識別碼；整數自動遞增主鍵','username':'登入帳號，不可重複','email':'會員電子郵件，不可重複','password_hash':'密碼雜湊值；不可輸出至 API 或報表','role':'角色：user 一般使用者、admin 管理者','approval_status':'會員審核：pending 待審核、approved 核准、rejected 拒絕、disabled 停用','created_at':'建立時間；SQLite CURRENT_TIMESTAMP 為 UTC','name':'資源名稱，不可重複','location':'所在位置','capacity':'可容納人數','description':'補充說明','active':'啟用旗標：1 啟用、0 停用','user_id':'預約會員，參照 users.id','title':'事件或警示標題','start_at':'預約開始時間；目前以 TEXT 保存','end_at':'預約結束時間；目前以 TEXT 保存','booking_type':'預約類型：personal 個人、room 會議廳','room_id':'會議廳識別碼；個人預約可為 NULL','notes':'預約備註','area':'實驗室或區域名稱，目前為文字而非外鍵','alert_type':'警示類型，例如個人防護、環境異常','severity':'嚴重程度，預設 medium；示範資料另有 high','detected_at':'偵測時間；預設 UTC CURRENT_TIMESTAMP','inspector':'稽核人員名稱，目前為文字而非會員外鍵','issue':'稽核問題描述','due_date':'改善期限，建議 YYYY-MM-DD；目前無格式約束'}
names.update({'member_review_history':'會員審核歷程','laboratories':'實驗室資源','cameras':'攝影機資源','schema_migrations':'資料庫升級版本'})
meaning.update({'must_change_password':'1 表示需先變更預設密碼，0 表示不需變更','actor_id':'審核操作者，參照 users.id','from_status':'審核前狀態','to_status':'審核後狀態：approved、rejected、disabled','laboratory_id':'實驗室外鍵，參照 laboratories.id','handler_id':'警示處理者，可空；參照 users.id','inspector_id':'稽核執行者會員 ID，可空；參照 users.id','device_index':'設備索引，非負整數；不代表實際鏡頭已連接','version':'已完成升級版本，整數主鍵','applied_at':'版本升級完成時間，UTC'})
pdfmetrics.registerFont(UnicodeCIDFont('MSung-Light'))
style=ParagraphStyle('中文',fontName='MSung-Light',fontSize=10,leading=16,spaceAfter=7)
small=ParagraphStyle('表格',parent=style,fontSize=8,leading=12,spaceAfter=0,wordWrap='CJK')
head=ParagraphStyle('標題',parent=style,fontSize=17,leading=24,spaceBefore=10,spaceAfter=10)
story=[]; md=[]
def section(title):
    md.append('\n## '+title+'\n'); story.append(Paragraph(html.escape(title),head))
def paragraph(text):
    md.append(text+'\n'); story.append(Paragraph(html.escape(text),style))
def grid(headers,rows,widths):
    md.append('| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|')
    md.extend('| '+' | '.join(str(v).replace('|','／') for v in row)+' |' for row in rows)
    data=[[Paragraph(html.escape(str(v)),small) for v in row] for row in [headers]+rows]
    table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce9f5')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b7c4d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([table,Spacer(1,12)])
md.append('# 台南大學實驗室監控系統：資料結構文件\n')
story.append(Paragraph('台南大學實驗室監控系統<br/>資料結構文件',head))
paragraph('文件日期：2026-10-06。來源：實際 SQLite schema 與 app/repositories/database.py；本報告不列出會員密碼雜湊或個人資料。')
section('一、資料庫建立與儲存')
paragraph('資料庫採 SQLite。Application Factory 啟動時呼叫 init_db，自動建立不存在的資料表，並為舊 users 表補上 approval_status。實際檔案為 instance/calendar.sqlite；名稱沿用舊系統，不代表資料庫僅供行事曆使用。既有資料保留，不重建或清空。')
paragraph('僅首次建立資料庫時初始化管理者與示範資料。admin 預設密碼為 admin@123、狀態 approved、must_change_password=1。重啟不覆寫密碼、不補回被清空的示範事件。schema_migrations 追蹤版本 1 至 3。')
section('二、資料表總覽')
grid(['資料表','用途','欄位數'],[(t,names[t],len(db.execute('PRAGMA table_info('+t+')').fetchall())) for t in tables],[110,300,80])
story.append(PageBreak())
section('三、資料關聯圖')
mermaid=['erDiagram','    USERS ||--o{ BOOKINGS : 建立','    ROOMS o|--o{ BOOKINGS : 指定','    USERS ||--o{ MEMBER_REVIEW_HISTORY : 申請者','    USERS ||--o{ MEMBER_REVIEW_HISTORY : 操作者','    LABORATORIES ||--o{ CAMERAS : 包含','    LABORATORIES o|--o{ SAFETY_ALERTS : 區域','    LABORATORIES o|--o{ AUDITS : 區域','    USERS o|--o{ SAFETY_ALERTS : 處理','    USERS o|--o{ AUDITS : 稽核']
for t in tables:
    mermaid.append('    '+t.upper()+' {')
    for c in db.execute('PRAGMA table_info('+t+')'):
        mermaid.append('        '+c['type']+' '+c['name']+(' PK' if c['pk'] else ''))
    mermaid.append('    }')
md.append('```mermaid\n'+'\n'.join(mermaid)+'\n```\n')
paragraph('實體關聯包含會員／預約、會員／審核歷程、實驗室／攝影機。警示與稽核新增可空的實驗室及會員外鍵，保留 area、inspector 文字快照，既有資料不猜測關聯。下圖為原資料表概覽；完整關聯見本節對照。')
diagram=Drawing(490,490)
positions={'users':(0,300),'bookings':(172,300),'rooms':(344,300),'safety_alerts':(0,0),'audits':(260,0)}
for table,(x,y) in positions.items():
    width=146 if table in ('users','bookings','rooms') else 225
    cols=db.execute('PRAGMA table_info('+table+')').fetchall()
    height=30+len(cols)*17
    diagram.add(Rect(x,y,width,height,fillColor=colors.HexColor('#edf3fa'),strokeColor=colors.HexColor('#8ca5c2')))
    diagram.add(String(x+8,y+height-18,table,fontName='MSung-Light',fontSize=11))
    diagram.add(Line(x,y+height-27,x+width,y+height-27,strokeColor=colors.HexColor('#8ca5c2')))
    for i,col in enumerate(cols):
        label=col['name']+(' [PK]' if col['pk'] else '')
        diagram.add(String(x+8,y+height-44-i*17,label,fontName='MSung-Light',fontSize=8))
diagram.add(Line(146,380,172,380,strokeColor=colors.HexColor('#3568aa')))
diagram.add(Polygon([172,380,166,384,166,376],fillColor=colors.HexColor('#3568aa')))
diagram.add(Line(344,380,318,380,strokeColor=colors.HexColor('#3568aa')))
diagram.add(Polygon([318,380,324,384,324,376],fillColor=colors.HexColor('#3568aa')))
diagram.add(String(5,265,'users.id → bookings.user_id：一對多',fontName='MSung-Light',fontSize=10))
diagram.add(String(5,245,'rooms.id → bookings.room_id：可選的一對多',fontName='MSung-Light',fontSize=10))
diagram.add(String(5,225,'警示與稽核已有可空的實驗室及會員外鍵。',fontName='MSung-Light',fontSize=10))
story.extend([diagram,Spacer(1,12)])
grid(['關聯來源','目標','用途'],[('users.id','member_review_history.user_id / actor_id','會員與操作者'),('laboratories.id','cameras.laboratory_id','必要設備歸屬'),('laboratories.id','safety_alerts / audits.laboratory_id','可空區域歸屬'),('users.id','safety_alerts.handler_id / audits.inspector_id','可空執行人員')],[100,230,160])
for t in tables:
    story.append(PageBreak()); section('四、'+names[t]+'：'+t)
    rows=[]
    for c in db.execute('PRAGMA table_info('+t+')'):
        desc=meaning.get(c['name'],'')
        if t=='member_review_history' and c['name']=='user_id':desc='被審核會員，參照 users.id'
        if t=='cameras' and c['name']=='name':desc='攝影機顯示名稱，不要求全域唯一'
        if c['name']=='status': desc={'bookings':'預約狀態：confirmed、pending、approved、rejected','safety_alerts':'警示處理狀態，預設 open；目前未以 CHECK 限制','audits':'改善處理狀態，預設 open；目前未以 CHECK 限制'}[t]
        rows.append((c['name'],c['type'],'主鍵' if c['pk'] else ('不可空' if c['notnull'] else '可空'),c['dflt_value'] or '無',desc))
    grid(['欄位','型別','空值／鍵','預設值','資料辭典'],rows,[95,55,55,100,185])
    indices=db.execute('PRAGMA index_list('+t+')').fetchall()
    paragraph('索引：'+('；'.join(i['name']+'（'+('唯一' if i['unique'] else '一般')+'）' for i in indices) if indices else '無額外索引；整數主鍵使用 SQLite rowid。'))
    ddl=db.execute('SELECT sql FROM sqlite_master WHERE name=?',(t,)).fetchone()[0]
    md.append('\n### 建表 SQL（實際資料庫）\n```sql\n'+ddl+';\n```\n')
    story.append(Paragraph('建表 SQL（實際資料庫）',style))
    for line in textwrap.wrap(ddl+';',width=76,break_long_words=False):
        story.append(Paragraph(html.escape(line),small))
    story.append(Spacer(1,10))
section('五、約束、日期與完整性')
paragraph('SQLite 採動態型別，TEXT 日期不是專用日期型別。CURRENT_TIMESTAMP 產生 UTC 的 YYYY-MM-DD HH:MM:SS；預約時間由輸入寫入，可能含 T，未保存時區。建議後續統一 UTC 保存、臺灣時間顯示。')
foreign=db.execute('PRAGMA foreign_keys').fetchone()[0]
paragraph('Flask get_db 已啟用 PRAGMA foreign_keys=ON；獨立工具連線預設可能為 OFF，需自行啟用。新表限制資源 active、設備索引與審核目標狀態；舊表仍以 Service 補充角色、日期與狀態驗證。')
paragraph('member_review_history 保存操作者、前後狀態及 UTC 時間；會員狀態與歷程應在同一交易更新。laboratories 與 cameras 保存資源，不保存 JPEG 或攝影機連線狀態。')
section('六、OpenCV 鏡頭串流與資料庫邊界')
paragraph('/video 已提供按鈕觸發的 OpenCV CAM 串流。CameraService 於主機記憶體保存鏡頭擁有者、state、message、frames 與最新 JPEG；不新增資料表，不保存影像或錄影。停止串流會釋放鏡頭，程序重啟後狀態重設。')
grid(['狀態欄位','資料型態','用途'],[('camera_index','整數','由 CAMERA_INDEX 設定鏡頭，預設 0'),('state','文字','stopped、starting、streaming、error'),('message','文字','繁體中文操作狀態與錯誤說明'),('frames','整數','本次啟動已擷取影格數'),('owner','整數或空值','控制鏡頭的會員 ID；只存在記憶體'),('frame','位元組或空值','最新 JPEG，串流傳送後不寫入 SQLite')],[100,80,310])
md.append('```mermaid\nflowchart LR\n    U[已核准會員] --> A[啟動按鈕與 CSRF 檢查]\n    A --> S[CameraService]\n    S --> C[OpenCV 主機鏡頭]\n    C --> J[記憶體 JPEG]\n    J --> V[MJPEG 頁面串流]\n    U --> D[(SQLite users 身分驗證)]\n```\n')
paragraph('鏡頭 API 使用 users 的核准狀態驗證存取；影像與 SQLite 資料流分離。cameras 為資源清單，與即時 CAM 控制不同；錄影索引及串流事件歷程仍未建立。')
section('七、資料生命週期與備份')
md.append('```mermaid\nflowchart LR\n    A[app.py 啟動] --> B[建立 SQLite 連線]\n    B --> C[建表與欄位補齊]\n    C --> D[初始化示範資料]\n    D --> E[Repository 讀寫]\n    E --> F[交易提交與備份]\n```\n')
paragraph('生命週期：app.py → Application Factory → init_db → 建表與必要欄位補齊 → 初始化 → Repository 讀寫。建議以 SQLite backup API 產生一致備份；不要在寫入期間直接複製單一資料庫檔案。Docker volume 掛載 /app/instance 可保留檔案。')
paragraph('既有資料庫有待升級版本時，自動在 instance/backups 產生 SQLite backup 與同名 JSON（建表 SQL、各表筆數）；先執行完整性與舊外鍵檢查，失敗時中止、不刪除資料。版本操作與標記使用同一交易，失敗回滾。')
paragraph('回滾操作：停止 Flask 與資料寫入，另存升級後資料庫，再以已驗證的備份還原 calendar.sqlite 並使用相容舊程式。勿在伺服器寫入期間直接覆蓋檔案；備份包含敏感會員雜湊，須妥善限制存取。')
section('八、檢查結果與後續改善')
result=db.execute('PRAGMA integrity_check').fetchone()[0]
paragraph('SQLite integrity_check：'+result+'。外鍵違規列數：'+str(len(db.execute('PRAGMA foreign_key_check').fetchall()))+'。')
paragraph('已註冊 close_db 至 Flask teardown_appcontext，結束時釋放連線。已完成 migration、審核歷程與資源 Schema；業務操作由本次 OpenSpec 後續任務補齊。舊 rooms／bookings 保留，尚未退役。')
db.close()
(root/'資料結構文件.md').write_text('\n'.join(md),encoding='utf-8')
def footer(canvas,doc):
    canvas.setFont('MSung-Light',9); canvas.drawString(42,24,'台南大學實驗室監控系統 | 資料結構文件'); canvas.drawRightString(553,24,str(doc.page))
SimpleDocTemplate(str(root/'資料結構文件.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print('已建立 Markdown 與 PDF')
