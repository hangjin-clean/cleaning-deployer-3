from pathlib import Path
import shutil
src=Path("admin.html")
dst=Path("out_gangnam")/"admin"/"index.html"
dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(src,dst)
print("[3호 admin] /admin/ 관리자 화면 생성")
