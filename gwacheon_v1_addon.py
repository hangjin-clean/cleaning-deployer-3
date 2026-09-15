# 3호 전국형 추가 페이지: 기존 3호 랜딩페이지 템플릿을 그대로 재사용
# 기존 gen.py / 메인 / 강남 페이지는 수정하지 않음
import gen as g

AREA_FULL = "경기도 과천시"
AREA = "과천시"
AREA_SHORT = "과천"
AREA_SLUG = "gwacheon"
DONGS = ["중앙동","별양동","부림동","과천동","문원동","갈현동"]
KEYS = [
    "office","hospital","academy","store","restaurant","school","gym","factory","salon",
    "stairs","cafe","daycare","bath","movein","completion","exterior","flood","fire","aircon"
]

def titles(key, label):
    custom = {
        "office": ["과천 사무실청소 업체추천","과천시 사무실 정기청소 업체","과천 사무실청소 전문업체","과천시 사무실청소업체 비용안내","과천시 사무실 정기관리 청소업체"],
        "hospital": ["과천 병원청소 업체추천","과천시 병원청소 업체비용","과천 병원정기청소 전문업체","과천시 병원청소업체","과천 개인병원청소 업체추천"],
        "academy": ["과천 학원청소 업체추천","과천시 학원 정기청소 업체","과천 학원청소 전문업체","과천시 학원청소업체 비용안내","과천시 교습소 스터디카페 청소업체"],
        "stairs": ["과천 계단청소 업체추천","과천시 계단청소 정기관리 업체","과천 빌라 계단청소 전문업체","과천시 계단청소업체 비용안내","과천시 상가 건물 계단청소 업체"],
    }
    return custom.get(key, [
        f"과천 {label} 업체추천",
        f"과천시 {label} 전문업체",
        f"과천 {label} 비용안내",
        f"과천시 {label} 정기관리",
        f"과천시 {label} 업체추천",
    ])

def page_path(key, n):
    return f"/published/gyeonggi/{AREA_SLUG}/{key}/v{n}/"

def make_page(v, key, n, title):
    path = page_path(key, n)
    items = []
    for vv in g.VERTICALS[:6]:
        ph = g.photo_list(vv)
        if ph:
            items.append((path, g.pub(ph[0]), f'{AREA_SHORT} {vv["kw"]}', f'{AREA_FULL} · {vv["kw"]}'))
    chips = ''.join(f'<a href="{path}">{g.e(d)}</a>' for d in DONGS)

    body = f'''<div class="hero"><div class="k">{AREA_FULL}</div>
<h1>{g.e(title)}</h1>
<p>{AREA}에서 필요한 {g.e(v["kw"])} 정보를 확인하고, 청소 종류와 업체 3곳의 연락처를 한 화면에서 비교할 수 있습니다. 견적은 각 업체에 직접 요청합니다.</p></div>
<section class="sec"><h2>청소 종류별</h2><p class="sub">업종 19종</p>{g.icon_grid()}</section>
<section class="sec"><h2>동별로 찾기</h2><p class="sub">{AREA} 주요 지역</p><div class="chips">{chips}</div></section>
{g.feed(items, f'최근 {AREA_SHORT} 작업 사례', '3호 랜딩페이지와 동일한 구성입니다')}
{g.company_rows(None, None)}'''

    desc = f"{title}. {AREA_FULL} {v['kw']} 안내와 청소업체 3곳 비교, 전화상담 및 무료견적 안내."
    crumbs = [(AREA, None)]
    jsonld = [{"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":g.HOST+path}]
    g.write(path, g.layout(title, desc, path, body, crumbs, jsonld, g.og_for(v)))
    return path

def main():
    made = []
    for idx, v in enumerate(g.VERTICALS[:19]):
        key = KEYS[idx]
        for n, title in enumerate(titles(key, v["kw"]), 1):
            made.append(make_page(v, key, n, title))
    print(f"[3호] 과천 동일 랜딩 템플릿 {len(made)}개 생성")

if __name__ == "__main__":
    main()
