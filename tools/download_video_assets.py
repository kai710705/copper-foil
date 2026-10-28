"""下載固定版本的前端資源，執行時不需要外網。"""
import urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'app'/'static'/'vendor'
root.mkdir(parents=True,exist_ok=True)
assets={'vue.global.prod.js':'vue@3.5.13/dist/vue.global.prod.js','axios.min.js':'axios@1.7.9/dist/axios.min.js','bootstrap.min.css':'bootstrap@5.3.3/dist/css/bootstrap.min.css','sweetalert2.all.min.js':'sweetalert2@11.15.10/dist/sweetalert2.all.min.js'}
for name,path in assets.items():
    with urllib.request.urlopen('https://cdn.jsdelivr.net/npm/'+path,timeout=60) as response:
        (root/name).write_bytes(response.read())
    print(name)
