from pathlib import Path
import html

OUT = Path("out_gangnam")
TARGET = OUT / "published" / "gyeonggi" / "gwacheon" / "hospital" / "v1"

def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    title = "과천 병원청소 업체추천"
    page = f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="경기도 과천시 병원·개인의원 정기청소 업체 비교와 상담 안내">
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Arial,'Noto Sans KR',sans-serif;background:#f6f8fc;color:#111}}
.wrap{{max-width:1080px;margin:auto;padding:28px 18px}} .hero,.card{{background:white;border:1px solid #e5e7eb;border-radius:22px;padding:28px;margin-bottom:18px}}
.badge{{color:#4f46e5;font-weight:800}} h1{{font-size:38px;margin:10px 0 14px}} h2{{margin-top:0}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .btn{{display:inline-block;padding:13px 18px;border-radius:12px;background:#4f46e5;color:white;text-decoration:none;font-weight:700}}
.muted{{color:#5f6673;line-height:1.75}} @media(max-width:760px){{.grid{{grid-template-columns:1fr}} h1{{font-size:30px}}}}
</style></head><body><main class="wrap">
<section class="hero"><div class="badge">경기도 과천시</div><h1>{html.escape(title)}</h1>
<p class="muted">과천시 병원·개인의원에서 필요한 오픈청소, 마감청소, 정기관리 업체를 비교해 보세요. 작업 범위와 방문 주기, 결제 방식 등을 확인한 뒤 상담할 수 있습니다.</p>
<a class="btn" href="/">청소비용비교 메인 보기</a></section>
<section class="card"><h2>과천 병원청소 확인 포인트</h2><p class="muted">진료실·대기실·복도·화장실·바닥 등 공간별 작업 범위, 주 1회부터 주 7회까지 필요한 관리 주기, 작업일지와 전후사진 제공 여부 등을 비교할 수 있습니다.</p></section>
<section class="grid">
<div class="card"><h2>행진크린</h2><p class="muted">법인·기업 대상 관리, 2인 1조 작업, 영업배상책임보험 1억 가입, 세금계산서·카드결제 상담.</p></div>
<div class="card"><h2>지니크린</h2><p class="muted">개인 사업장 중심 직접 관리, 병원·학원·사무실 등 정기청소 상담.</p></div>
<div class="card"><h2>청소뱅크</h2><p class="muted">사업장 정기관리와 병원청소 상담, 세금계산서·카드결제 가능 여부 확인.</p></div>
</section>
<section class="card"><h2>병원청소 상담 전 확인</h2><p class="muted">평수, 원하는 요일과 시간대, 주당 방문 횟수, 화장실 및 공용공간 포함 여부를 정리하면 보다 정확한 상담에 도움이 됩니다.</p></section>
</main></body></html>"""
    (TARGET / "index.html").write_text(page, encoding="utf-8")
    print("[3호 add-on] 과천 병원청소 v1 완성형 페이지 생성")

if __name__ == "__main__":
    main()
