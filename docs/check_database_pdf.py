from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium
root=Path(__file__).parent
path=root/'資料結構文件.pdf'
r=PdfReader(path)
print('頁數',len(r.pages))
text=''.join(p.extract_text() for p in r.pages)
assert '資料結構文件' in text and 'approval_status' in text and 'audits' in text
out=root.parent/'tmp'/'pdfs'; out.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(str(path))
for i in range(len(doc)):
    doc[i].render(scale=1.2).to_pil().save(out/f'database-{i+1}.png')
print('中文與欄位文字檢查通過；已渲染所有頁面')
