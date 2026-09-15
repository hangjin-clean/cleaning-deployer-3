#!/usr/bin/env python3
"""
강남구 청소업체 비교 페이지 생성기.
법정동 14개 × 업종 19개 = 266개 동 페이지 + 업종 허브 19 + 동 허브 14 + 루트를 out/ 에 정적 HTML로 뽑는다.
실행: HOST=https://도메인 python3 gen.py   (HOST 생략 시 pages.dev 기본값)
"""
import os, json, re, shutil, html, itertools, hashlib
from pathlib import Path

GU_SLUG = os.environ.get('CB_GU', 'gangnam')   # 어느 구를 만들지: gangnam / gangdong
HOST = (os.environ.get('HOST') or os.environ.get('URL') or f'https://{GU_SLUG}-cleaning.pages.dev').rstrip('/')
OUT = Path(__file__).parent / f'out_{GU_SLUG}'
ASSETS = Path(__file__).parent / 'assets'
INDEXNOW_KEY = os.environ.get('INDEXNOW_KEY', 'a7c1e4f09b3d4e6f8a2b5c7d9e1f3a5b')

# ───────── 업체 3곳 (고정) ─────────
COMPANIES = [
    dict(key='hangjin', name='행진크린', logo='hangjin.png', tel='010-3300-7431',
         tag='법인 운영 · 기업 사업장 청소',
         feats=['정기관리 · 입주청소 · 대청소', '준공청소 · 인테리어 후 청소', '영업배상책임보험 가입', '카드결제 · 세금계산서 발행'],
         point='법인으로 운영돼 사무실·상업시설·프랜차이즈처럼 관리 일정이 정해진 사업장에 맞춰 상담이 가능합니다.',
         form='https://docs.google.com/forms/d/e/1FAIpQLSd3uNlt1Mqu8xUtuxfSqNTV8Nx8yi-LNDIT2gwSx7RO6WTGJA/viewform',
         home='https://xn--sy2b170ac4etyf.com/', blog='https://blog.naver.com/goldvine'),
    dict(key='jini', name='지니크린', logo='jini.png', tel='010-5926-1764',
         tag='개인 사업장 맞춤 청소',
         feats=['정기관리 · 입주청소 · 대청소', '준공청소 · 인테리어 후 청소', '업종별 일정 · 관리주기 협의', '카드결제 · 세금계산서 발행'],
         point='이용량과 영업시간을 보고 관리주기와 작업범위를 조정하는 방식이라 소규모 개인 사업장에 맞습니다.',
         form='https://docs.google.com/forms/d/e/1FAIpQLScb4iyLy6tOMDkxPv7rnsJbnh_zrqZNN7iQY-xdV5Ofpwhn5A/viewform',
         home='https://jinicleaning.com/', blog='https://blog.naver.com/choija1023'),
    dict(key='cb', name='청소뱅크', logo='cleaningbank.png', tel='010-6856-0158',
         tag='병원 · 개인 사업장 정기관리',
         feats=['무료 방문견적 상담', '정기관리 · 입주청소 · 대청소', '준공청소 · 인테리어 후 청소', '카드결제 · 세금계산서 발행'],
         point='병원과 개인 사업장 정기관리가 중심이고, 방문견적을 먼저 받아 관리 범위를 정하는 방식입니다.',
         form='https://docs.google.com/forms/d/e/1FAIpQLSdHW-3aXFkPAz7eE46jdBGemgc6CHKebGbTGl3fKtj3iu6GfA/viewform',
         home='https://cleaning-bank.imweb.me/', blog='https://blog.naver.com/palhana'),
]

# ───────── 법정동 (stevejkang/legal-area-code, is_deleted=0) ─────────
# trait: 동네 성격 한 줄. 업종별 문단에 섞어 동마다 다른 본문을 만든다. kind: 업종 hook 선택 키.
GANGNAM_DONGS = [
    dict(slug='yeoksam',   name='역삼동',   code='1168010100', trait='테헤란로를 따라 오피스 빌딩과 상가, 식당이 가장 촘촘하게 모인 곳', kind='office'),
    dict(slug='gaepo',     name='개포동',   code='1168010300', trait='재건축이 끝난 대단지 아파트가 잇따라 입주하는 곳', kind='resi'),
    dict(slug='cheongdam', name='청담동',   code='1168010400', trait='명품거리와 미용실, 피부과, 고급 카페가 밀집한 곳', kind='beauty'),
    dict(slug='samseong',  name='삼성동',   code='1168010500', trait='코엑스와 오피스 타워, 호텔이 모인 업무 중심지', kind='office'),
    dict(slug='daechi',    name='대치동',   code='1168010600', trait='은마사거리와 한티역 일대에 학원이 가장 많이 모인 곳', kind='edu'),
    dict(slug='sinsa',     name='신사동',   code='1168010700', trait='가로수길 매장과 카페, 압구정 인접 병의원이 섞인 곳', kind='retail'),
    dict(slug='nonhyeon',  name='논현동',   code='1168010800', trait='가구거리와 학동역 상가, 병의원과 사무실이 혼재한 곳', kind='mixed'),
    dict(slug='apgujeong', name='압구정동', code='1168011000', trait='성형외과와 피부과, 미용실이 집중된 곳', kind='beauty'),
    dict(slug='segok',     name='세곡동',   code='1168011100', trait='보금자리 신규 아파트 단지와 단독·다세대 주택이 함께 있는 곳', kind='resi'),
    dict(slug='jagok',     name='자곡동',   code='1168011200', trait='신축 아파트 단지와 어린이집, 근린 상가가 들어선 신주거지', kind='resi'),
    dict(slug='yulhyeon',  name='율현동',   code='1168011300', trait='세곡·자곡과 이어진 소규모 신규 주거 지역', kind='resi'),
    dict(slug='irwon',     name='일원동',   code='1168011400', trait='대형 종합병원과 아파트 단지, 학교가 함께 있는 곳', kind='medical'),
    dict(slug='suseo',     name='수서동',   code='1168011500', trait='SRT 수서역을 중심으로 주거와 업무 개발이 진행 중인 곳', kind='mixed'),
    dict(slug='dogok',     name='도곡동',   code='1168011800', trait='고층 주상복합과 아파트가 많고 대치동 학원가와 맞닿은 곳', kind='resi'),
]
GANGDONG_DONGS = [
    dict(slug='cheonho',  name='천호동', code='1174010900', trait='천호역 로데오거리와 백화점 상권에 상가·병의원·학원이 밀집한 곳', kind='mixed'),
    dict(slug='gildong',  name='길동',   code='1174010500', trait='길동사거리 상가와 빌라·다세대 주거가 섞인 곳', kind='mixed'),
    dict(slug='dunchon',  name='둔촌동', code='1174010600', trait='둔촌주공 재건축 대단지가 입주한 신축 아파트 지역', kind='resi'),
    dict(slug='amsa',     name='암사동', code='1174010700', trait='암사역 상권과 다세대 주거, 선사유적지가 있는 곳', kind='resi'),
    dict(slug='seongnae', name='성내동', code='1174010800', trait='강동구청 주변 상가와 원룸·다세대가 밀집한 곳', kind='mixed'),
    dict(slug='myeongil', name='명일동', code='1174010100', trait='명일역 학원가와 아파트 단지가 함께 있는 곳', kind='edu'),
    dict(slug='godeok',   name='고덕동', code='1174010200', trait='재건축 신축 대단지 아파트가 잇따라 입주한 곳', kind='resi'),
    dict(slug='sangil',   name='상일동', code='1174010300', trait='고덕비즈밸리 업무단지와 신축 아파트가 들어선 곳', kind='office'),
    dict(slug='gangil',   name='강일동', code='1174011000', trait='강일지구 신규 아파트와 물류·업무시설이 있는 곳', kind='resi'),
]
GANGBUK_DONGS = [
    dict(slug='mia',   name='미아동', code='1130510100', trait='미아사거리 상권과 뉴타운 신축 아파트, 학원이 함께 있는 곳', kind='mixed'),
    dict(slug='beon',  name='번동',   code='1130510200', trait='번동 아파트 단지와 다세대 주거, 근린 상가가 섞인 곳', kind='resi'),
    dict(slug='suyu',  name='수유동', code='1130510300', trait='수유역 먹자골목과 상가, 병의원이 밀집한 강북 중심 상권', kind='mixed'),
    dict(slug='ui',    name='우이동', code='1130510400', trait='북한산 자락의 주거지와 카페·음식점이 있는 곳', kind='resi'),
]
GANGSEO_DONGS = [
    dict(slug='yeomchang',   name='염창동',   code='1150010100', trait='한강변 아파트 단지와 염창역 상가가 있는 곳', kind='resi'),
    dict(slug='deungchon',   name='등촌동',   code='1150010200', trait='등촌역 상권과 아파트·다세대 주거가 섞인 곳', kind='mixed'),
    dict(slug='hwagok',      name='화곡동',   code='1150010300', trait='강서구에서 가장 인구가 많고 빌라·다세대와 상가가 밀집한 곳', kind='mixed'),
    dict(slug='gayang',      name='가양동',   code='1150010400', trait='가양역 일대 아파트 단지와 지식산업센터가 있는 곳', kind='office'),
    dict(slug='magok',       name='마곡동',   code='1150010500', trait='마곡지구 기업 연구소·오피스와 신축 아파트가 모인 업무 중심지', kind='office'),
    dict(slug='naebalsan',   name='내발산동', code='1150010600', trait='발산역 상권과 학원, 아파트 단지가 함께 있는 곳', kind='edu'),
    dict(slug='oebalsan',    name='외발산동', code='1150010700', trait='공항 인접 물류·업무시설과 주거가 섞인 곳', kind='mixed'),
    dict(slug='gonghang',    name='공항동',   code='1150010800', trait='김포공항 주변 상가와 주거, 항공 관련 시설이 있는 곳', kind='mixed'),
    dict(slug='banghwa',     name='방화동',   code='1150010900', trait='방화역 상권과 아파트·다세대 주거가 있는 곳', kind='resi'),
    dict(slug='gaehwa',      name='개화동',   code='1150011000', trait='개화산 자락의 주거지와 소규모 작업장이 있는 곳', kind='resi'),
    dict(slug='gwahae',      name='과해동',   code='1150011100', trait='김포공항 서측의 물류·업무시설 지역', kind='office'),
    dict(slug='ogok',        name='오곡동',   code='1150011200', trait='공항 인접 물류창고와 업무시설이 있는 곳', kind='office'),
    dict(slug='osoe',        name='오쇠동',   code='1150011300', trait='공항 남측의 업무·물류시설 지역', kind='office'),
]
GWANAK_DONGS = [
    dict(slug='bongcheon', name='봉천동', code='1162010100', trait='서울대입구역 상권과 원룸·다세대, 학원이 밀집한 곳', kind='mixed'),
    dict(slug='sillim',    name='신림동', code='1162010200', trait='신림역 먹자골목과 고시촌, 원룸 건물이 가장 많은 곳', kind='mixed'),
    dict(slug='namhyeon',  name='남현동', code='1162010300', trait='사당역 인접 주거지와 소규모 상가가 있는 곳', kind='resi'),
]
GWANGJIN_DONGS = [
    dict(slug='junggok',   name='중곡동', code='1121510100', trait='중곡역 상권과 다세대·빌라 주거가 밀집한 곳', kind='mixed'),
    dict(slug='neung',     name='능동',   code='1121510200', trait='어린이대공원 주변 주거지와 세종대 인근 상가가 있는 곳', kind='resi'),
    dict(slug='guui',      name='구의동', code='1121510300', trait='강변역 테크노마트 상권과 아파트 단지가 함께 있는 곳', kind='mixed'),
    dict(slug='gwangjang', name='광장동', code='1121510400', trait='한강변 아파트 단지와 학교, 학원이 모인 주거지', kind='edu'),
    dict(slug='jayang',    name='자양동', code='1121510500', trait='건대입구 상권과 원룸·오피스텔, 아파트가 섞인 곳', kind='mixed'),
    dict(slug='hwayang',   name='화양동', code='1121510700', trait='건국대 앞 먹자골목과 원룸 건물이 가장 밀집한 곳', kind='mixed'),
    dict(slug='gunja',     name='군자동', code='1121510900', trait='군자역 상권과 세종대 인근 주거, 소규모 상가가 있는 곳', kind='resi'),
]
GURO_DONGS = [
    dict(slug='sindorim',  name='신도림동', code='1153010100', trait='신도림역 대형 쇼핑몰과 오피스, 주상복합이 모인 곳', kind='office'),
    dict(slug='guro',      name='구로동',   code='1153010200', trait='구로디지털단지 지식산업센터와 상가, 원룸이 밀집한 곳', kind='office'),
    dict(slug='garibong',  name='가리봉동', code='1153010300', trait='디지털단지 인접 다세대 주거와 상가가 섞인 곳', kind='mixed'),
    dict(slug='gocheok',   name='고척동',   code='1153010600', trait='고척돔 주변 아파트 단지와 학교, 학원이 있는 곳', kind='edu'),
    dict(slug='gaebong',   name='개봉동',   code='1153010700', trait='개봉역 상권과 아파트·빌라 주거가 함께 있는 곳', kind='resi'),
    dict(slug='oryu',      name='오류동',   code='1153010800', trait='오류동역 상권과 아파트 단지, 다세대 주거가 있는 곳', kind='resi'),
    dict(slug='gung',      name='궁동',     code='1153010900', trait='온수 인근 저층 주거지와 학교가 있는 곳', kind='resi'),
    dict(slug='onsu',      name='온수동',   code='1153011000', trait='온수역 일대 공장·창고와 주거가 섞인 곳', kind='mixed'),
    dict(slug='cheonwang', name='천왕동',   code='1153011100', trait='천왕지구 신축 아파트 단지가 들어선 곳', kind='resi'),
    dict(slug='hang',      name='항동',     code='1153011200', trait='항동지구 신규 아파트와 공원, 학교가 있는 신주거지', kind='resi'),
]
GEUMCHEON_DONGS = [
    dict(slug='gasan',  name='가산동', code='1154510100', trait='가산디지털단지 지식산업센터와 아울렛, 오피스가 밀집한 곳', kind='office'),
    dict(slug='doksan', name='독산동', code='1154510200', trait='독산역 상권과 아파트·다세대 주거, 소규모 공장이 섞인 곳', kind='mixed'),
    dict(slug='siheung', name='시흥동', code='1154510300', trait='시흥사거리 상권과 아파트 단지, 빌라 주거가 있는 곳', kind='resi'),
]
REGIONS = {
    'gangnam':  dict(name='강남구', sample='역삼·삼성·대치·논현', dongs=GANGNAM_DONGS),
    'gangdong': dict(name='강동구', sample='천호·길동·둔촌·암사', dongs=GANGDONG_DONGS),
    'gangbuk':  dict(name='강북구', sample='미아·번동·수유·우이', dongs=GANGBUK_DONGS),
    'gangseo':  dict(name='강서구', sample='화곡·마곡·등촌·가양', dongs=GANGSEO_DONGS),
    'gwanak':   dict(name='관악구', sample='봉천·신림·남현', dongs=GWANAK_DONGS),
    'gwangjin': dict(name='광진구', sample='구의·자양·화양·광장', dongs=GWANGJIN_DONGS),
    'guro':     dict(name='구로구', sample='구로·신도림·개봉·오류', dongs=GURO_DONGS),
    'geumcheon': dict(name='금천구', sample='가산·독산·시흥', dongs=GEUMCHEON_DONGS),
}
GU = REGIONS[GU_SLUG]; GN = GU['name']; DONGS = GU['dongs']

# ───────── 업종 19개 ─────────
# kw: 검색어(=H1 핵심), photos: assets/svc/{code} 사진 수, hook: 동 성격(kind)별 한 문장
def V(code, slug, kw, short, intro, points, faq, hook, desc):
    return dict(code=code, slug=slug, kw=kw, short=short, intro=intro, points=points, faq=faq, hook=hook, desc=desc)

VERTICALS = [
 V('office','office-cleaning','사무실청소','사무실',
   ['사무실청소는 직원이 없는 시간에 들어가서 출근 전까지 끝내는 게 기본입니다. 야간이나 주말에 바닥 왁스 작업과 카펫 세척을 몰아서 하고, 평일에는 책상 주변과 탕비실, 화장실 위주로 짧게 관리합니다.',
    '견적은 평수보다 바닥 재질과 파티션 수, 화장실 개수로 갈립니다. 같은 50평이라도 카펫 사무실과 데코타일 사무실은 작업 시간이 다르니 도면이나 사진을 먼저 보내는 게 빠릅니다.'],
   ['바닥 왁스·카펫 세척은 월 1회 야간 작업', '책상·모니터·전화기 상판은 매회 소독 티슈 사용', '탕비실 개수대와 냉장고 내부는 주 1회', '분리수거장과 흡연구역 정리 포함 여부 확인'],
   [('주 몇 회가 적당한가요?','20명 내외 사무실은 주 2~3회가 보통이고, 화장실을 직접 관리하지 않는 사무실은 매일 방문으로 잡습니다.'),
    ('야간 작업 시 보안은 어떻게 하나요?','출입 카드나 비밀번호를 담당자 한 명에게만 부여하고 작업 후 사진으로 보고하는 방식으로 진행합니다.'),
    ('입주 전 사무실 청소도 되나요?','인테리어 후 분진 제거와 입주 전 청소는 정기관리와 별도 견적으로 1회 진행합니다.')],
   dict(office='오피스 빌딩이 많아 야간 출입 절차와 엘리베이터 사용 시간을 건물 관리사무소와 먼저 맞춰야 합니다.',
        resi='주거지라 소규모 사무실이 많고, 오피스텔 사무실은 주 1회 방문으로 시작하는 경우가 많습니다.',
        beauty='매장과 사무실이 한 건물에 섞여 있어 영업시간 밖 작업 시간대를 정확히 잡아야 합니다.',
        edu='학원 사무실은 수업이 없는 오전이 작업 시간이고, 교무실과 상담실을 함께 관리합니다.',
        retail='매장 뒤 사무 공간까지 한 번에 관리하는 계약이 많습니다.',
        mixed='상가 건물의 사무실은 공용 계단·화장실 관리 포함 여부를 먼저 정해야 견적이 정확합니다.',
        medical='병원 사무동과 연구실은 일반 사무실보다 소독 기준이 높습니다.'),
   '야간·주말 왁스 작업과 평일 상시 관리 기준으로 비교.'),
 V('hospital','hospital-cleaning','병원청소','병원',
   ['병원청소는 진료가 끝난 뒤부터 다음 날 오픈 전 사이에 2인 1조로 들어갑니다. 진료실·대기실·복도·화장실을 구역으로 나누고, 구역마다 걸레와 도구를 따로 써서 교차 오염을 막는 게 핵심입니다.',
    '의료 폐기물은 병원이 직접 처리하고 청소 업체는 일반 쓰레기와 바닥, 손잡이, 접수대 소독을 맡습니다. 어디까지가 청소 범위인지 계약서에 적어두는 게 서로 편합니다.'],
   ['진료실·대기실·화장실 도구 분리 사용', '손잡이·접수대·의자 팔걸이 소독제 닦기', '바닥은 소독 성분 세제로 습식 청소', '의료 폐기물은 청소 범위에서 제외'],
   [('진료 중에도 청소가 가능한가요?','대기실과 화장실은 진료 중 짧게 관리하고, 진료실은 진료 종료 후 작업합니다.'),
    ('소독제는 어떤 걸 쓰나요?','병원에서 지정한 소독제가 있으면 그걸 쓰고, 없으면 4급 암모늄 계열 표면 소독제를 씁니다.'),
    ('개원 전 청소도 되나요?','인테리어 후 개원 청소는 분진 제거와 장비 외부 닦기까지 1회 작업으로 진행합니다.')],
   dict(office='오피스 빌딩 안에 있는 의원은 건물 야간 출입 규정에 맞춰 작업 시간을 정합니다.',
        resi='아파트 상가 소아과·내과가 많고, 대기실 바닥과 장난감 소독을 함께 요청하는 경우가 많습니다.',
        beauty='성형외과·피부과가 밀집해 수술실 인접 구역 청소 기준을 병원과 먼저 확인합니다.',
        edu='학원가 인근 정형외과·안과는 저녁 진료가 늦어 밤 10시 이후 작업이 많습니다.',
        retail='상가 건물 의원은 공용 복도까지 관리하는지 건물주와 범위를 정합니다.',
        mixed='병의원과 사무실이 한 건물에 섞여 있어 의원 구역만 별도 도구로 관리합니다.',
        medical='대형 종합병원 주변 개인 의원과 약국이 많아 정기관리 수요가 꾸준합니다.'),
   '진료 후 2인 1조 작업, 구역별 도구 분리 기준으로 비교.'),
 V('academy','academy-cleaning','학원청소','학원',
   ['학원청소는 수업이 없는 오전이나 심야에 교실·복도·화장실을 관리합니다. 책상 낙서와 껌, 바닥 발자국이 가장 많이 쌓이는 곳이라 책상 상판 닦기와 바닥 습식 청소를 매회 넣습니다.',
    '수강생 이동량에 따라 화장실 관리 횟수를 정합니다. 시험 기간처럼 학생이 몰리는 시기에는 임시로 횟수를 늘리는 식으로 조정합니다.'],
   ['책상 상판·의자 매회 닦기', '복도·계단 발자국 습식 청소', '화장실은 수강생 수에 맞춰 횟수 조정', '강의실 화이트보드·마커 정리'],
   [('수업 중에는 안 들어오나요?','수업 중에는 화장실만 관리하고 교실은 수업 종료 후 작업합니다.'),
    ('방학 특강 기간에 횟수를 늘릴 수 있나요?','기간을 정해 주 5회로 늘렸다가 다시 줄이는 방식으로 조정 가능합니다.'),
    ('독서실·스터디카페도 되나요?','독서실은 소음 문제로 새벽 시간대 작업으로 잡습니다.')],
   dict(office='오피스 상권의 직장인 대상 학원은 밤 10시 이후 작업이 기본입니다.',
        resi='아파트 단지 상가 학원은 초등 저학년 비중이 커 바닥과 손잡이 소독을 함께 넣습니다.',
        beauty='어학원과 성인 대상 학원이 많아 오전 시간 작업으로 잡습니다.',
        edu='학원이 가장 밀집한 곳이라 같은 건물 여러 학원을 묶어 관리하는 계약이 많습니다.',
        retail='매장 위층 학원은 건물 공용 계단 관리를 포함할지 먼저 정합니다.',
        mixed='건물 내 학원 여러 곳을 한 업체가 함께 맡는 경우가 많습니다.',
        medical='병원 인근 아파트 단지 학원은 오전 시간대 작업이 많습니다.'),
   '수업 없는 시간 작업, 학생 수 기준 화장실 횟수로 비교.'),
 V('retail','retail-cleaning','매장청소','매장',
   ['매장청소는 오픈 전 1~2시간이 작업 시간입니다. 출입문 유리와 진열대, 바닥이 손님 눈에 가장 먼저 들어오는 곳이라 이 세 가지를 매회 기본으로 잡습니다.',
    '점포 단위로 계약하고 진열 상품은 만지지 않습니다. 쇼윈도 외부 유리와 간판 하단은 월 1회 별도 작업으로 넣는 경우가 많습니다.'],
   ['출입문·쇼윈도 유리 매회', '진열대 상판·하단 먼지 제거', '바닥 습식 청소 후 건조', '피팅룸·창고 정리는 협의'],
   [('상품 진열은 건드리나요?','진열 상품은 만지지 않고 진열대 표면과 주변만 관리합니다.'),
    ('오픈 전 몇 시부터 가능한가요?','보통 오픈 2시간 전부터 들어가며 열쇠나 비밀번호를 담당자와 공유합니다.'),
    ('프랜차이즈 여러 점포도 되나요?','점포별로 일정을 짜서 한 업체가 묶어 관리할 수 있습니다.')],
   dict(office='오피스 상권 매장은 점심·퇴근 시간 이용이 몰려 오전 작업이 기본입니다.',
        resi='단지 상가 매장은 소규모라 주 1~2회 방문으로 잡습니다.',
        beauty='명품·편집숍은 진열 관리가 엄격해 유리와 바닥만 맡는 계약이 많습니다.',
        edu='학원가 문구·편의점은 저녁 이용이 많아 심야 작업으로 잡습니다.',
        retail='가로수길 매장은 오픈이 늦어 오전 9~11시 작업 시간이 넉넉한 편입니다.',
        mixed='가구 매장은 전시 가구 표면 관리 방식을 먼저 확인합니다.',
        medical='병원 주변 약국·편의점은 이용 시간이 길어 새벽 작업이 많습니다.'),
   '오픈 전 유리·진열대·바닥 기본 작업으로 비교.'),
 V('restaurant','restaurant-cleaning','식당청소','식당',
   ['식당청소는 홀 정기관리와 주방 후드·덕트 1회 작업을 나눠 봅니다. 홀은 마감 후 바닥 기름기 제거와 테이블·의자 닦기, 주방은 후드 필터와 벽면 기름때를 분기 1회 벗겨내는 식입니다.',
    '후드 청소는 화재 예방과 직결되니 마지막 작업일을 적어두고 주기를 정하는 게 좋습니다. 배수구와 그리스트랩은 냄새 원인이라 정기관리에 포함할지 확인합니다.'],
   ['홀 바닥 기름기 제거는 알칼리 세제 습식', '후드·덕트·필터는 분기 1회 별도', '배수구·그리스트랩 포함 여부 확인', '마감 후 또는 오픈 전 작업'],
   [('후드 청소만 따로 되나요?','후드·덕트만 1회 작업으로 진행 가능하고 정기관리와 묶으면 단가가 낮아집니다.'),
    ('영업 중 작업은 안 되나요?','홀은 마감 후, 주방은 화기 사용이 없는 시간에만 작업합니다.'),
    ('위생점검 앞두고 급하게도 되나요?','일정이 비면 1회 대청소로 잡을 수 있으니 날짜를 먼저 알려주세요.')],
   dict(office='테헤란로 식당은 점심 회전이 커 오전 10시 전 홀 작업으로 잡습니다.',
        resi='단지 상가 식당은 배달 비중이 높아 주방 기름때 관리가 중심입니다.',
        beauty='고급 레스토랑은 유리·조명·테이블 마감 기준이 높아 작업 시간을 넉넉히 잡습니다.',
        edu='학원가 분식·패스트푸드는 회전이 빨라 바닥 기름기 관리 횟수를 늘립니다.',
        retail='가로수길 식당·바는 새벽 마감이 많아 오전 작업 시간을 조정합니다.',
        mixed='상가 식당 밀집 건물은 공용 배수구 냄새 관리를 함께 요청하는 경우가 많습니다.',
        medical='병원 주변 식당은 아침 영업이 이르니 심야 작업으로 잡습니다.'),
   '홀 정기관리와 후드·덕트 1회 작업을 나눠 비교.'),
 V('school','school-cleaning','학교청소','학교',
   ['학교청소는 방학에 몰아서 하는 대청소와 학기 중 특별실 관리로 나뉩니다. 방학 대청소는 교실 바닥 왁스, 창문 유리, 급식실 후드까지 한 번에 진행합니다.',
    '학기 중에는 체육관·강당·급식실처럼 관리자가 따로 없는 공간을 주 1회 관리하는 계약이 많습니다. 공공기관은 견적서와 세금계산서 양식을 먼저 맞춥니다.'],
   ['방학 대청소: 교실 왁스·창문·급식실 후드', '학기 중 특별실·체육관 주 1회', '유리창은 고소 작업 안전장비 필수', '견적서·세금계산서 양식 사전 확인'],
   [('방학 대청소는 며칠 걸리나요?','학급 수에 따라 다르지만 24학급 기준 3~5일로 잡습니다.'),
    ('학기 중 작업은 어떻게 하나요?','수업 시간을 피해 방과 후에 특별실 위주로 작업합니다.'),
    ('사립 유치원·대안학교도 되나요?','규모와 상관없이 같은 방식으로 견적을 냅니다.')],
   dict(office='업무지구라 학교보다는 직업훈련 기관과 평생교육시설이 대상입니다.',
        resi='아파트 단지 안 초등학교와 유치원이 많아 방학 대청소 문의가 몰립니다.',
        beauty='국제학교와 외국인학교 시설은 관리 기준을 먼저 확인합니다.',
        edu='학교와 학원이 함께 있어 방학 시기에 일정이 겹치니 미리 잡아야 합니다.',
        retail='학교 수가 적어 인근 동 학교와 함께 일정을 잡습니다.',
        mixed='초·중학교와 사립 교육시설이 섞여 있어 시설별로 견적을 따로 냅니다.',
        medical='병원 인근 학교는 통학 안전상 작업 차량 진입 시간을 학교와 맞춥니다.'),
   '방학 대청소와 학기 중 특별실 관리 기준으로 비교.'),
 V('gym','gym-cleaning','헬스장청소','헬스장',
   ['헬스장청소는 기구 손잡이와 매트, 샤워실 물때가 핵심입니다. 새벽 오픈 전에 기구 소독과 바닥 닦기를 하고, 샤워실과 탈의실은 이용이 뜸한 낮 시간에 한 번 더 관리합니다.',
    '고무 바닥과 우레탄 바닥은 세제가 다르고, 거울 얼룩은 매회 잡아야 합니다. 락커 내부와 사우나 시설 포함 여부로 견적이 달라집니다.'],
   ['기구 손잡이·매트 매회 소독', '샤워실 물때·배수구 곰팡이 관리', '거울 얼룩·바닥 땀자국 매회', '락커·사우나 포함 여부 확인'],
   [('새벽 몇 시부터 가능한가요?','오픈 1~2시간 전부터 작업하며 24시간 헬스장은 이용이 가장 적은 새벽 3~5시로 잡습니다.'),
    ('필라테스·요가 스튜디오도 되나요?','매트와 기구 소독 중심으로 같은 방식으로 관리합니다.'),
    ('샤워실만 별도로 되나요?','샤워실·탈의실만 주 2~3회 관리하는 계약도 가능합니다.')],
   dict(office='직장인 이용이 많아 출근 전 새벽 시간대 작업이 기본입니다.',
        resi='아파트 단지 인근 헬스장은 주부·시니어 이용이 많아 오전 10시 전 작업으로 잡습니다.',
        beauty='PT 스튜디오와 필라테스가 많아 매트·소도구 소독 중심 관리가 많습니다.',
        edu='학원가 인근 헬스장은 저녁 이용이 몰려 낮 시간 샤워실 관리를 넣습니다.',
        retail='소규모 스튜디오가 많아 주 2~3회 방문으로 시작합니다.',
        mixed='상가 건물 헬스장은 공용 화장실 관리 포함 여부를 정합니다.',
        medical='재활 운동센터는 기구 소독 기준이 높아 소독제 종류를 먼저 확인합니다.'),
   '새벽 기구 소독과 샤워실 물때 관리 기준으로 비교.'),
 V('factory','factory-cleaning','공장청소','공장',
   ['공장청소는 가동을 멈추는 날에 맞춰 바닥 기름과 분진, 설비 외부를 한 번에 처리합니다. 안전화·안전모 착용과 작업 전 안전교육이 기본이고, 설비 내부는 손대지 않습니다.',
    '고소 작업이 들어가는 천장 배관과 조명은 별도 장비가 필요해 견적을 따로 냅니다. 사무동과 식당 정기관리를 함께 묶는 경우가 많습니다.'],
   ['가동 정지일에 맞춰 일정', '바닥 기름·분진은 산업용 세제·스크러버', '설비 내부 제외, 외부만 작업', '천장 배관·조명은 고소 장비 별도'],
   [('가동 중에도 작업이 되나요?','사무동과 식당, 화장실은 가동 중에도 가능하고 생산 구역은 정지일에만 작업합니다.'),
    ('안전교육은 누가 하나요?','공장 측 안전관리자 교육을 받고 작업하며, 없으면 업체 자체 교육으로 대체합니다.'),
    ('폐기물 처리도 하나요?','일반 쓰레기 정리까지이고 산업 폐기물은 공장이 처리합니다.')],
   dict(office='제조 공장보다는 데이터센터·기계실 같은 설비 공간이 대상입니다.',
        resi='주거지라 공장은 거의 없고 소규모 작업장이나 창고가 대상입니다.',
        beauty='공장보다는 스튜디오와 촬영장 같은 넓은 작업 공간이 대상입니다.',
        edu='공장은 없고 실습실이나 인쇄소 같은 소규모 작업장이 대상입니다.',
        retail='매장 물류 창고와 작업장이 대상이고 지게차 동선을 확인합니다.',
        mixed='가구 창고와 작업장이 있어 분진 관리 중심으로 견적을 냅니다.',
        medical='병원 인근 물류 창고와 기계실이 대상입니다.'),
   '가동 정지일 일정과 안전 기준으로 비교.'),
 V('salon','salon-cleaning','미용실청소','미용실',
   ['미용실청소는 모발 먼지와 염색약 얼룩이 핵심입니다. 바닥 모발은 진공으로 먼저 걷고 습식으로 마무리하며, 염색약이 튄 벽과 샴푸대는 전용 세제로 닦아야 얼룩이 남지 않습니다.',
    '거울과 조명 유리는 매회, 샴푸대 배수구 모발 제거는 주 1회가 기본입니다. 오픈 전 1시간 작업이 많고 예약제 살롱은 예약 없는 오전을 잡습니다.'],
   ['바닥 모발 진공 후 습식', '샴푸대·벽면 염색약 얼룩 전용 세제', '거울·조명 유리 매회', '샴푸대 배수구 모발 제거 주 1회'],
   [('염색약 얼룩이 오래돼도 지워지나요?','바닥재에 따라 다르지만 대부분 전용 세제로 옅어지고, 안 되는 부분은 견적 때 미리 말씀드립니다.'),
    ('네일샵·속눈썹샵도 되나요?','시술대와 조명 관리 중심으로 같은 방식으로 관리합니다.'),
    ('영업 중에 들어올 수 있나요?','오픈 전이 기본이고 영업 중에는 화장실만 관리합니다.')],
   dict(office='직장인 대상 살롱은 점심·퇴근 예약이 몰려 오전 10시 전 작업입니다.',
        resi='단지 상가 미용실은 소규모라 주 1~2회 방문이 많습니다.',
        beauty='미용실이 가장 밀집한 곳이라 같은 건물 여러 매장을 묶어 관리합니다.',
        edu='학원가 인근 미용실은 저녁 예약이 많아 오전 작업으로 잡습니다.',
        retail='가로수길 살롱은 인테리어 마감재가 다양해 바닥재를 먼저 확인합니다.',
        mixed='상가 미용실은 공용 화장실 관리 포함 여부를 정합니다.',
        medical='병원 인근 미용실은 오전 이용이 많아 심야 작업으로 잡습니다.'),
   '모발·염색약 얼룩 관리와 오픈 전 작업으로 비교.'),
 V('stair','stair-cleaning','계단청소','계단',
   ['계단청소는 건물주나 관리인이 월 2~4회로 계약하는 게 보통입니다. 계단 바닥 습식 청소와 난간 닦기, 각 층 복도와 우편함 주변, 출입구 유리까지가 기본 범위입니다.',
    '엘리베이터 내부와 지하 주차장 포함 여부로 견적이 갈립니다. 분리수거장 정리는 별도 항목으로 잡는 경우가 많습니다.'],
   ['계단·복도 습식 청소, 난간 닦기', '출입구 유리·우편함 주변', '엘리베이터 내부 포함 여부', '분리수거장 정리는 별도'],
   [('월 몇 회가 적당한가요?','5층 이하 상가주택은 월 2회, 이용이 많은 근린상가는 월 4회로 잡습니다.'),
    ('원룸 건물도 되나요?','세대 수와 층수만 알려주시면 같은 방식으로 견적을 냅니다.'),
    ('입주민이 없는 시간에 오나요?','오전 시간대 작업이 기본이고 시간 지정도 가능합니다.')],
   dict(office='중소형 오피스 빌딩은 공용 화장실까지 묶어 주 2회로 계약하는 경우가 많습니다.',
        resi='단독·다세대 주택이 많아 건물주 직접 계약이 대부분입니다.',
        beauty='매장 건물은 출입구 유리와 로비 관리를 중요하게 봅니다.',
        edu='학원 건물은 학생 통행이 많아 월 4회 이상으로 잡습니다.',
        retail='상가 건물은 야간 이용이 많아 오전 작업으로 잡습니다.',
        mixed='상가주택이 많아 계단과 옥상 출입구까지 관리하는 경우가 많습니다.',
        medical='병원 인근 원룸 건물은 세대 수가 많아 월 4회로 잡습니다.'),
   '월 2~4회 계약 기준, 엘리베이터·주차장 포함 여부로 비교.'),
 V('cafe','cafe-cleaning','카페청소','카페',
   ['카페청소는 오픈 전 바닥과 테이블, 화장실이 기본이고 커피 머신 주변 얼룩과 우유 자국이 쌓이는 바 안쪽이 핵심입니다. 원두 가루와 시럽 자국은 매회 닦지 않으면 끈적임이 남습니다.',
    '테라스와 유리창은 주 1회, 제빙기 외부와 냉장고 하단은 월 1회로 잡습니다. 머신 내부 세척은 청소 범위가 아니라 카페가 직접 관리합니다.'],
   ['바 안쪽 우유·시럽 자국 매회', '바닥·테이블·화장실 오픈 전', '유리창·테라스 주 1회', '커피 머신 내부는 범위 제외'],
   [('오픈 시간이 이른데 가능한가요?','오픈 1시간 전 작업이 기본이고 새벽 시간 지정도 가능합니다.'),
    ('베이커리·디저트 매장도 되나요?','주방 기름때 관리를 추가해 같은 방식으로 관리합니다.'),
    ('스터디카페도 되나요?','좌석과 책상 소독 중심으로 새벽 시간대 작업합니다.')],
   dict(office='오피스 카페는 아침 이용이 많아 오픈 1시간 전 작업이 빠듯하니 전날 마감 후 작업도 검토합니다.',
        resi='단지 상가 카페는 소규모라 주 2~3회 방문으로 잡습니다.',
        beauty='디저트 카페와 브런치 매장이 많아 주방 관리를 함께 넣습니다.',
        edu='학원가 스터디카페가 많고 좌석 소독 중심으로 새벽 작업이 기본입니다.',
        retail='가로수길 카페는 테라스와 유리창 비중이 커 주 1회 유리 작업을 넣습니다.',
        mixed='상가 카페는 공용 화장실 관리 포함 여부를 먼저 정합니다.',
        medical='병원 앞 카페는 아침 6시 오픈이 많아 심야 작업으로 잡습니다.'),
   '바 안쪽 얼룩 관리와 오픈 전 작업 기준으로 비교.'),
 V('daycare','daycare-cleaning','어린이집청소','어린이집',
   ['어린이집청소는 아이들이 없는 저녁이나 주말에 들어가고, 세제는 친환경 인증 제품을 씁니다. 바닥 매트와 교구 표면, 손잡이 소독이 기본이고 화장실은 아이 눈높이 변기와 세면대까지 닦습니다.',
    '방학이나 휴원일에 매트 하부와 창틀, 커튼까지 대청소로 잡습니다. 조리실은 식당 기준으로 후드와 배수구를 관리합니다.'],
   ['친환경 인증 세제만 사용', '바닥 매트·교구·손잡이 소독', '아이 눈높이 변기·세면대', '휴원일 매트 하부·창틀 대청소'],
   [('세제 성분을 확인할 수 있나요?','사용 세제 목록과 인증서를 사전에 전달합니다.'),
    ('원아가 있을 때 작업하나요?','원아 하원 후 저녁이나 주말에만 작업합니다.'),
    ('유치원·키즈카페도 되나요?','같은 기준으로 관리하며 키즈카페는 볼풀·놀이기구 소독을 추가합니다.')],
   dict(office='직장어린이집이 많아 건물 출입 절차를 먼저 확인합니다.',
        resi='신축 단지 안 어린이집이 많아 정기관리 문의가 꾸준합니다.',
        beauty='어린이집보다는 놀이학교와 영어유치원이 대상입니다.',
        edu='영어유치원과 놀이학교가 많아 교구 소독 기준을 먼저 확인합니다.',
        retail='소규모 가정어린이집이 대상이라 주 1회 방문으로 시작합니다.',
        mixed='상가 어린이집은 공용 계단 관리 포함 여부를 정합니다.',
        medical='병원 직장어린이집은 소독 기준이 높아 소독제를 먼저 확인합니다.'),
   '친환경 세제와 휴원일 대청소 기준으로 비교.'),
 V('bath','bath-cleaning','목욕탕청소','목욕탕',
   ['목욕탕청소는 물때와 곰팡이가 굳기 전에 잡는 게 전부입니다. 영업 종료 후 탕 내부 배수, 타일 줄눈 산성 세제 작업, 사우나 목재 관리를 하고 오픈 전에 헹굼까지 끝냅니다.',
    '탈의실과 락커, 파우더룸은 별도 구역으로 매일 관리하고 배관 냄새는 배수구 트랩 관리로 잡습니다. 찜질방 시설 포함 여부로 견적이 크게 갈립니다.'],
   ['탕 배수 후 타일 줄눈 산성 세제', '사우나 목재는 전용 세제', '탈의실·락커·파우더룸 매일', '찜질방 포함 여부 확인'],
   [('영업을 안 쉬는데 가능한가요?','24시간 시설은 이용이 가장 적은 새벽에 구역을 나눠 순차 작업합니다.'),
    ('곰팡이가 이미 심한데 되나요?','1회 대청소로 벗겨낸 뒤 정기관리로 넘어가는 방식을 권합니다.'),
    ('헬스장 샤워실만도 되나요?','샤워실·탈의실만 주 2~3회 관리하는 계약이 가능합니다.')],
   dict(office='대형 목욕탕보다는 사무실 빌딩 샤워실과 피트니스 사우나가 대상입니다.',
        resi='아파트 단지 커뮤니티 사우나와 동네 목욕탕이 대상입니다.',
        beauty='스파와 마사지샵의 샤워 시설이 대상이고 마감 기준이 높습니다.',
        edu='목욕탕은 적고 헬스장 샤워실과 찜질방이 대상입니다.',
        retail='호텔·스파 시설의 샤워실이 대상입니다.',
        mixed='동네 목욕탕과 찜질방이 대상이고 24시간 시설이 많습니다.',
        medical='병원 인근 찜질방과 사우나가 대상입니다.'),
   '물때·곰팡이 관리와 영업 시간 작업 방식으로 비교.'),
 V('movein','move-in-cleaning','입주청소','입주',
   ['입주청소는 짐이 들어오기 전 빈 집에서 하루에 끝냅니다. 주방 후드와 싱크 하부, 욕실 실리콘 곰팡이, 창틀과 베란다 배수구, 붙박이장 내부까지가 기본 범위입니다.',
    '새 아파트는 시공 분진과 스티커 자국, 구축은 찌든 때와 곰팡이가 중심이라 작업 방식이 다릅니다. 평수와 신축·구축 여부, 확장 여부를 알려주면 견적이 바로 나옵니다.'],
   ['주방 후드·싱크 하부·냉장고장 내부', '욕실 실리콘 곰팡이·줄눈', '창틀·베란다 배수구·방충망', '붙박이장·신발장 내부'],
   [('이사 당일에도 되나요?','짐이 들어오면 작업이 안 되니 하루 전이 가장 좋습니다.'),
    ('새집증후군 시공도 같이 되나요?','입주청소 후 별도 시공으로 연결 가능하니 견적 때 말씀해 주세요.'),
    ('원룸·오피스텔도 되나요?','평수에 맞춰 반나절 작업으로 진행합니다.')],
   dict(office='오피스텔 입주가 많아 소형 평수 반나절 작업이 대부분입니다.',
        resi='신축 대단지 입주가 이어져 시공 분진 제거 중심의 새 아파트 입주청소가 많습니다.',
        beauty='고급 빌라와 주상복합이 많아 마감재 보호 기준을 먼저 확인합니다.',
        edu='학군 이사가 많아 학기 시작 전 2월과 8월에 예약이 몰립니다.',
        retail='주거보다 매장·사무실 입주 전 청소 문의가 많습니다.',
        mixed='다세대와 빌라가 많아 구축 입주청소 비중이 높습니다.',
        medical='병원 인근 아파트와 원룸 입주가 많아 연중 문의가 꾸준합니다.'),
   '짐 들어오기 전 하루 작업, 신축·구축 방식 차이로 비교.'),
 V('newbuild','construction-cleaning','준공청소','준공',
   ['준공청소는 공사가 끝난 뒤 입주나 오픈 전에 분진과 시멘트 자국, 보양 스티커, 페인트 튐을 걷어내는 작업입니다. 공정이 모두 끝난 뒤에 들어가야 두 번 일하지 않습니다.',
    '인테리어 후 청소는 매장·사무실·병원 오픈 전에 같은 방식으로 진행합니다. 유리 스티커 제거와 바닥 보양재 자국이 시간을 가장 많이 잡아먹습니다.'],
   ['공정 완료 후 작업 일정', '분진·시멘트 자국·페인트 튐 제거', '유리 스티커·보양재 자국', '바닥 마감재별 세제 선택'],
   [('공사 중간에도 되나요?','마감 공정이 끝나기 전에는 분진이 다시 쌓여 권하지 않습니다.'),
    ('견적은 뭘 보고 내나요?','평수, 바닥 마감재, 유리 면적, 층고를 보고 냅니다.'),
    ('오픈 전날도 되나요?','일정이 비면 가능하지만 최소 2일 전 예약을 권합니다.')],
   dict(office='사무실 인테리어 후 오픈 전 청소가 대부분이고 야간 작업이 많습니다.',
        resi='신축 아파트 세대 준공청소와 상가 인테리어 후 청소가 함께 몰립니다.',
        beauty='매장·살롱 인테리어 마감재가 고급이라 마감재별 세제를 먼저 확인합니다.',
        edu='학원 인테리어 후 개원 전 청소가 많고 방학 직전에 몰립니다.',
        retail='매장 리뉴얼 후 오픈 전 청소가 많아 유리 스티커 제거 비중이 큽니다.',
        mixed='병의원과 사무실 인테리어 후 청소가 섞여 있습니다.',
        medical='개원 전 병원 준공청소가 많고 소독 작업을 함께 넣습니다.'),
   '공정 완료 후 분진·스티커·보양재 제거 기준으로 비교.'),
 V('exterior','exterior-cleaning','외벽청소','외벽',
   ['외벽청소는 로프 작업과 고소작업차 중 건물 구조에 맞는 방식을 고릅니다. 유리 커튼월은 로프, 저층 상가는 고소작업차나 사다리로 접근하고 간판과 캐노피 세척을 함께 넣습니다.',
    '안전관리 계획서와 보험 가입 여부를 먼저 확인해야 합니다. 도로 점용이 필요하면 신고 절차가 들어가니 일정을 여유 있게 잡습니다.'],
   ['로프 또는 고소작업차 방식 선택', '유리·석재·판넬 재질별 세제', '간판·캐노피 세척 포함', '안전관리 계획서·보험 확인'],
   [('몇 층까지 가능한가요?','로프 작업은 층수 제한이 거의 없고 고소작업차는 도로 폭에 따라 다릅니다.'),
    ('비 오면 어떻게 하나요?','우천 시 작업이 취소되고 다음 가능일로 옮깁니다.'),
    ('간판만 따로 되나요?','간판·캐노피만 1회 작업으로 가능합니다.')],
   dict(office='유리 커튼월 빌딩이 많아 로프 작업 비중이 높습니다.',
        resi='아파트 외벽보다는 단지 상가 저층 외벽과 간판이 대상입니다.',
        beauty='석재·유리 마감 매장이 많아 재질별 세제를 먼저 확인합니다.',
        edu='학원 건물 간판 세척 문의가 많고 도로 폭이 좁아 로프 작업이 많습니다.',
        retail='가로수길 저층 매장은 사다리와 고소작업차로 접근합니다.',
        mixed='상가주택 외벽과 간판 세척이 대상이고 도로 점용 신고가 필요할 수 있습니다.',
        medical='병원 건물 외벽은 진료 시간을 피해 주말 작업이 많습니다.'),
   '로프·고소작업차 방식과 안전 확인 기준으로 비교.'),
 V('flood','flood-cleaning','침수청소','침수',
   ['침수청소는 물이 빠진 뒤 48시간 안에 건조를 시작해야 곰팡이를 막습니다. 오염수 배출, 젖은 마감재 제거, 소독, 강제 건조 순서로 진행하고 건조가 끝나야 복구 공사가 가능합니다.',
    '보험 청구용 사진과 작업 기록을 남기니 처음부터 말씀해 주세요. 지하층은 배수 펌프와 제습기 대수로 견적이 갈립니다.'],
   ['48시간 내 건조 시작', '오염수 배출·젖은 마감재 제거', '소독 후 제습기·송풍기 강제 건조', '보험 청구용 사진·기록'],
   [('얼마나 빨리 올 수 있나요?','침수는 우선 배정하고 당일 방문을 기본으로 잡습니다.'),
    ('냄새는 없어지나요?','건조와 소독이 끝나면 대부분 사라지고 남는 경우 원인을 찾아 추가 작업합니다.'),
    ('복구 공사도 하나요?','청소와 건조까지이고 공사 업체를 연결해 드립니다.')],
   dict(office='지하 기계실과 주차장 침수가 많아 배수 펌프 작업이 중심입니다.',
        resi='반지하와 다세대 주택 침수가 많아 젖은 장판·벽지 제거가 중심입니다.',
        beauty='매장 지하층 침수가 많아 재고 이동과 건조를 함께 진행합니다.',
        edu='학원 지하 강의실 침수가 많아 카펫 제거와 건조가 중심입니다.',
        retail='상가 지하 창고 침수가 많아 재고 정리를 함께 요청합니다.',
        mixed='상가주택 지하층 침수가 많고 배수 펌프 작업이 중심입니다.',
        medical='병원 지하 침수는 소독 기준이 높아 소독제를 먼저 확인합니다.'),
   '48시간 내 건조와 보험 기록 기준으로 비교.'),
 V('fire','fire-cleaning','화재청소','화재',
   ['화재청소는 그을음과 냄새를 잡는 작업입니다. 마른 그을음은 건식 스펀지로 먼저 걷어내고 그다음 습식으로 닦아야 번지지 않습니다. 냄새는 오존이나 광촉매 처리로 마무리합니다.',
    '소방서 화재 조사가 끝난 뒤에 작업이 가능하고, 보험 청구용 사진과 작업 기록을 남깁니다. 타버린 마감재 철거는 별도 견적입니다.'],
   ['화재 조사 종료 후 작업', '건식 스펀지 후 습식 순서', '오존·광촉매 냄새 처리', '타버린 마감재 철거 별도'],
   [('냄새가 완전히 없어지나요?','그을음 제거 후 냄새 처리를 하면 대부분 사라지고 남으면 추가 처리합니다.'),
    ('가구도 살릴 수 있나요?','표면 그을음은 닦을 수 있고 스며든 냄새는 개별 처리로 확인합니다.'),
    ('작업 기간은 얼마나 되나요?','규모에 따라 1~5일이고 냄새 처리는 하루 더 잡습니다.')],
   dict(office='사무실 화재는 서류와 전산 장비 그을음 처리를 함께 요청합니다.',
        resi='주택 화재가 많아 가구와 벽지 그을음 처리가 중심입니다.',
        beauty='매장 화재는 진열 상품 처리 여부를 먼저 정합니다.',
        edu='학원 화재는 개원 일정에 맞춰 냄새 처리를 서두르는 경우가 많습니다.',
        retail='매장 화재는 오픈 일정에 맞춰 냄새 처리를 우선합니다.',
        mixed='식당 주방 화재가 많아 후드와 덕트 그을음 처리가 중심입니다.',
        medical='병원 화재는 소독과 냄새 처리를 함께 진행합니다.'),
   '그을음 건식·습식 순서와 냄새 처리 기준으로 비교.'),
 V('aircon','aircon-cleaning','에어컨청소','에어컨',
   ['에어컨청소는 분해 세척이 전부입니다. 커버만 닦는 건 청소가 아니고 열교환기와 송풍 팬, 드레인을 분해해 고압 세척해야 냄새와 곰팡이가 잡힙니다. 천장형은 4방향 팬 분해까지 들어갑니다.',
    '대수가 많은 사업장은 한 번에 잡아야 단가가 내려갑니다. 실외기 세척은 별도 항목이고 가스 충전은 청소 범위가 아닙니다.'],
   ['열교환기·송풍 팬·드레인 분해 세척', '천장형 4방향 팬 분해', '실외기 세척 별도', '가스 충전은 범위 제외'],
   [('작업 시간은 얼마나 걸리나요?','벽걸이 1대 40분, 천장형 1대 1시간 내외로 잡습니다.'),
    ('영업 중에도 되나요?','영업 중에는 소음과 물 사용이 있어 마감 후나 오픈 전을 권합니다.'),
    ('여름 전에 예약해야 하나요?','5~6월에 몰리니 4월 예약을 권합니다.')],
   dict(office='사무실 천장형 대수가 많아 야간에 한 번에 작업하는 계약이 많습니다.',
        resi='아파트 벽걸이·스탠드 세척이 많고 신축 단지 입주 후 첫 여름에 몰립니다.',
        beauty='매장 천장형이 많고 냄새에 민감해 봄마다 정기 세척을 잡습니다.',
        edu='학원 천장형 대수가 많아 방학 직전에 예약이 몰립니다.',
        retail='매장 오픈 전 새벽 작업이 많습니다.',
        mixed='식당 에어컨은 기름때가 섞여 세척 시간이 더 걸립니다.',
        medical='병원 천장형은 진료 후 작업하고 소독을 함께 넣습니다.'),
   '분해 세척 범위와 대수별 일정 기준으로 비교.'),
]

# ───────── 공통 레이아웃 (숨고·짐싸 톤: 흰 카드 / 연회색 바탕 / 인디고 포인트 / 행 리스트 + 견적 버튼) ─────────
BRAND = '청소비용비교'
ICON = {'office':'🏢','hospital':'🏥','academy':'📚','retail':'🛍️','restaurant':'🍽️','school':'🏫','gym':'🏋️','factory':'🏭','salon':'💇',
        'stair':'🪜','cafe':'☕','daycare':'🧸','bath':'🛁','movein':'🚚','newbuild':'🏗️','exterior':'🧗','flood':'🌊','fire':'🔥','aircon':'❄️'}
CSS = """
:root{--p:#4B4DFF;--p2:#6C6EFF;--pl:#EEF0FF;--bg:#F5F6FA;--card:#fff;--tx:#1B1D2A;--mu:#6B7280;--bd:#E9EBF2;--ok:#16A34A}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,Inter,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.6;font-feature-settings:"tnum";padding-bottom:76px}
a{color:inherit;text-decoration:none}img{max-width:100%}
.wrap{max-width:780px;margin:0 auto;padding:0 16px}
.top{position:sticky;top:0;z-index:20;background:#fff;border-bottom:1px solid var(--bd)}.top .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.brand{font-weight:900;font-size:22px;color:var(--p);letter-spacing:-.02em;font-style:italic}.brand b{color:var(--p2)}
.top .btn{padding:8px 14px;font-size:13px}
.crumb{font-size:12px;color:var(--mu);padding:12px 0 0}.crumb a:hover{color:var(--p)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:12px 18px;border-radius:12px;font-weight:700;font-size:15px;border:1px solid transparent;cursor:pointer;white-space:nowrap}
.btn.p{background:var(--p);color:#fff}.btn.p:hover{background:#3B3DE6}.btn.s{background:#F1F2F7;color:var(--tx)}.btn.o{background:#fff;border-color:var(--bd);color:var(--tx)}
.hero{background:#fff;border-radius:20px;padding:26px 22px;margin:16px 0;border:1px solid var(--bd)}
.hero .k{font-size:13px;color:var(--p);font-weight:700}.hero h1{font-size:26px;line-height:1.3;margin:6px 0 10px;letter-spacing:-.01em}.hero h1 em{font-style:normal;color:var(--p)}
.hero p{margin:0;color:var(--mu);font-size:15px}.hero .cta{display:flex;gap:8px;margin-top:18px}.hero .cta .btn{flex:1}
.sec{margin:26px 0}.sec h2{font-size:19px;margin:0 0 4px;letter-spacing:-.01em}.sec .sub{font-size:13px;color:var(--mu);margin:0 0 14px}
.panel{background:#fff;border-radius:18px;border:1px solid var(--bd);overflow:hidden}
.row{display:flex;align-items:center;gap:14px;padding:16px 18px;border-top:1px solid var(--bd)}.row:first-child{border-top:0}
.row .lg{width:52px;height:52px;border-radius:14px;background:var(--pl);display:flex;align-items:center;justify-content:center;flex:none;overflow:hidden}.row .lg img{max-width:44px;max-height:30px}
.row .tx{flex:1;min-width:0}.row .tx b{display:block;font-size:16px}.row .tx span{display:block;font-size:13px;color:var(--mu);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row .btn{padding:9px 14px;font-size:13px;border-radius:10px}
.sub-links{display:flex;gap:6px;padding:0 18px 14px 84px;margin-top:-6px;flex-wrap:wrap}.sub-links a{font-size:12px;color:var(--mu);background:#F5F6FA;border-radius:8px;padding:4px 9px}.sub-links a.tel{color:var(--p);font-weight:700;background:var(--pl)}
.scroll{display:flex;gap:10px;overflow-x:auto;padding:4px 2px 10px;scrollbar-width:none;-webkit-overflow-scrolling:touch}.scroll::-webkit-scrollbar{display:none}
.cat{flex:none;width:76px;text-align:center;font-size:12px;color:var(--tx)}.cat i{display:flex;align-items:center;justify-content:center;width:56px;height:56px;margin:0 auto 6px;border-radius:16px;background:#fff;border:1px solid var(--bd);font-style:normal;font-size:26px}.cat.on i{background:var(--pl);border-color:var(--p)}.cat.on{color:var(--p);font-weight:700}
.icons{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.icons a{background:#fff;border:1px solid var(--bd);border-radius:14px;padding:12px 4px;text-align:center;font-size:12px}.icons a i{display:block;font-size:24px;font-style:normal;margin-bottom:4px}
@media(max-width:480px){.icons{grid-template-columns:repeat(4,1fr)}}
.feed{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.feed a{display:block}.feed .ph{aspect-ratio:1/1;border-radius:14px;overflow:hidden;background:#E5E7EB}.feed img{width:100%;height:100%;object-fit:cover;display:block}.feed b{display:block;font-size:13px;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.feed span{font-size:12px;color:var(--mu)}
@media(max-width:480px){.feed{grid-template-columns:repeat(2,1fr)}.feed a:nth-child(n+5){display:none}}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.tile{background:#fff;border:1px solid var(--bd);border-radius:16px;padding:16px;font-size:14px;line-height:1.5}.tile i{display:block;font-size:24px;font-style:normal;margin-bottom:8px}.tile small{display:block;color:var(--mu);font-size:12px;margin-bottom:2px}
.guide{background:#fff;border:1px solid var(--bd);border-radius:18px;padding:20px}.guide p{margin:0 0 12px;font-size:15px}.guide p:last-child{margin:0}.guide .pt{background:var(--pl);border-radius:12px;padding:12px 14px;font-size:14px}
details{background:#fff;border:1px solid var(--bd);border-radius:14px;padding:0 18px;margin-bottom:8px}summary{cursor:pointer;font-weight:700;padding:14px 0;font-size:15px;list-style:none;display:flex;justify-content:space-between}summary::after{content:"+";color:var(--mu)}details[open] summary::after{content:"–"}details div{padding:0 0 14px;color:var(--mu);font-size:14px}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chips a{background:#fff;border:1px solid var(--bd);border-radius:999px;padding:8px 14px;font-size:13px}.chips a:hover{border-color:var(--p);color:var(--p)}
.chips a.on{background:var(--tx);color:#fff;border-color:var(--tx)}
footer{background:#fff;border-top:1px solid var(--bd);margin-top:30px;padding:26px 0 30px;font-size:12px;color:var(--mu)}footer .brand{font-size:18px;display:block;margin-bottom:8px}footer .fl{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 12px}footer .fl a{color:var(--tx);font-weight:600}
.bar{position:fixed;left:0;right:0;bottom:0;z-index:30;background:#fff;border-top:1px solid var(--bd);padding:10px 16px calc(10px + env(safe-area-inset-bottom))}.bar .in{max-width:780px;margin:0 auto;display:flex;gap:8px}.bar .btn{flex:1}
@media(min-width:781px){.hero h1{font-size:30px}}
"""
FAV = "data:image/svg+xml," + html.escape('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#4B4DFF"/><path d="M8 20l6-9 4 6 3-4 3 7" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>', quote=True)

def e(s): return html.escape(s, quote=True)

def layout(title, desc, path, body, crumbs, jsonld, og_image=None, bar=True):
    url = HOST + path
    crumb_html = ' › '.join(f'<a href="{e(h)}">{e(t)}</a>' if h else e(t) for t, h in crumbs)
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    og = og_image or HOST + '/assets/logos/cleaningbank.png'
    c0 = COMPANIES[0]
    barhtml = f'<div class="bar"><div class="in"><a class="btn o" href="tel:{c0["tel"].replace("-","")}">📞 전화 상담</a><a class="btn p" href="#compare">무료 견적 받기</a></div></div>' if bar else ''
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(url)}"><meta property="og:image" content="{e(og)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">
<link rel="icon" href="{FAV}"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{CSS}</style>{ld}</head><body>
<header class="top"><div class="wrap"><a class="brand" href="/">{BRAND}</a><a class="btn p" href="#compare">견적받기</a></div></header>
<main class="wrap"><nav class="crumb">{crumb_html}</nav>{body}</main>
<footer><div class="wrap"><span class="brand">{BRAND}</span>{GN} 청소업체 비교 안내 페이지. 견적·계약은 각 업체와 직접 진행하며 본 페이지는 상담을 중개하지 않습니다.<div class="fl"><a href="/">홈</a>{''.join(f'<a href="{c["home"]}" target="_blank" rel="noopener">{e(c["name"])}</a>' for c in COMPANIES)}<a href="/sitemap.xml">사이트맵</a></div>© 2026 {BRAND}</div></footer>
{barhtml}</body></html>'''

def company_rows(dong, v):
    label = f"{dong['name']} {v['kw']}" if (dong and v) else (f"{GN} {v['kw']}" if v else '{GN} 청소')
    rows = ''
    for c in COMPANIES:
        rows += f'''<div class="row"><div class="lg"><img src="/assets/logos/{c['logo']}" alt="{e(c['name'])}"></div><div class="tx"><b>{e(c['name'])}</b><span>{e(c['tag'])} · {e(c['feats'][0])}</span></div><a class="btn p" href="{c['form']}" target="_blank" rel="noopener">견적받기</a></div>
<div class="sub-links"><a class="tel" href="tel:{c['tel'].replace('-','')}">📞 {c['tel']}</a><a href="{c['home']}" target="_blank" rel="noopener">홈페이지</a><a href="{c['blog']}" target="_blank" rel="noopener">블로그</a></div>'''
    return f'<section class="sec" id="compare"><h2>{e(label)} 업체 3곳</h2><p class="sub">견적은 각 업체에서 직접 받습니다. 전화·폼 어느 쪽이든 됩니다.</p><div class="panel">{rows}</div></section>'

def photo_list(v):
    d = ASSETS / 'svc' / v['code']
    return sorted(p for p in d.iterdir() if not p.name.startswith('.')) if d.exists() else []

def pub(p):
    """사진 공개 URL. 파일 내용 해시를 이름에 넣는다 (immutable 캐시라 이름이 같으면 브라우저가 새 사진을 안 받음)."""
    h = hashlib.md5(p.read_bytes()).hexdigest()[:8]
    return f'/assets/svc/{p.parent.name}/{h}{p.suffix.lower()}'

def feed(items, title, sub=''):
    if not items: return ''
    cards = ''.join(f'<a href="{href}"><div class="ph"><img src="{src}" alt="{e(cap)}" loading="lazy"></div><b>{e(cap)}</b><span>{e(meta)}</span></a>' for href, src, cap, meta in items)
    return f'<section class="sec"><h2>{e(title)}</h2><p class="sub">{e(sub)}</p><div class="feed">{cards}</div></section>'

def cat_scroller(d, cur):
    items = ''.join(f'<a class="cat{" on" if v is cur else ""}" href="{page_path(d, v)}"><i>{ICON[v["code"]]}</i>{e(v["short"])}</a>' for v in VERTICALS)
    return f'<section class="sec"><h2>{e(d["name"])} 다른 청소</h2><div class="scroll">{items}</div></section>'

def icon_grid(d=None):
    items = ''.join(f'<a href="{page_path(d, v) if d else vert_path(v)}"><i>{ICON[v["code"]]}</i>{e(v["short"])}</a>' for v in VERTICALS)
    return f'<div class="icons">{items}</div>'

def og_for(v):
    ph = photo_list(v)
    return HOST + pub(ph[0]) if ph else None

def dong_path(d): return f'/{d["slug"]}/'
def vert_path(v): return f'/{v["slug"]}/'
def page_path(d, v): return f'/{d["slug"]}/{v["slug"]}/'

def write(path, html_str):
    p = OUT / path.strip('/') / 'index.html' if path != '/' else OUT / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(html_str, encoding='utf-8')

# ───────── 동×업종 페이지 ─────────
def dong_vert_page(d, v, di):
    path = page_path(d, v)
    title = f"{d['name']} {v['kw']} 업체 비교견적 · {GN} 청소업체 3곳"
    desc = f"{d['name']} {v['kw']} 견적을 행진크린·지니크린·청소뱅크 3곳에서 비교. {v['desc']} {d['name']}은 {d['trait']}."
    hook = v['hook'][d['kind']]
    ph = photo_list(v)
    # 동마다 다른 사진 3장: 동 순번만큼 밀어서 고른다 (같은 업종이라도 동별로 사진이 달라짐)
    pick = [ph[(di*3 + i) % len(ph)] for i in range(min(3, len(ph)))] if ph else []
    items = [(page_path(d, v), pub(p), f'{d["name"]} {v["kw"]} 작업 {i+1}', f'서울 {GN} {d["name"]} · {v["kw"]}') for i, p in enumerate(pick)]
    tiles = ''.join(f'<div class="tile"><i>{"✅🧹🕐📋"[i]}</i><small>작업 포인트 {i+1}</small>{e(p)}</div>' for i, p in enumerate(v['points']))
    faq_html = ''.join(f'<details{" open" if i==0 else ""}><summary>{e(q)}</summary><div>{e(a)}</div></details>' for i, (q, a) in enumerate(v['faq']))
    others_d = ''.join(f'<a href="{page_path(o, v)}"{" class=on" if o is d else ""}>{e(o["name"])}</a>' for o in DONGS)
    c0 = COMPANIES[0]
    body = f'''<div class="hero"><div class="k">서울 {GN} {e(d['name'])}</div><h1>{e(d['name'])} <em>{e(v['kw'])}</em>,<br>한 번에 견적 끝내기</h1>
<p>{e(d['name'])}은 {e(d['trait'])}입니다. {e(hook)}</p>
<div class="cta"><a class="btn p" href="#compare">업체 3곳 비교</a><a class="btn s" href="tel:{c0['tel'].replace('-','')}">전화 상담</a></div></div>
{company_rows(d, v)}
{cat_scroller(d, v)}
{feed(items, f'{d["name"]} 주변 {v["kw"]} 작업 사례', '실제 현장 사진입니다')}
<section class="sec"><h2>{e(v['kw'])} 안심 포인트</h2><p class="sub">견적 전에 이것부터 확인하세요</p><div class="tiles">{tiles}</div></section>
<section class="sec"><h2>{e(d['name'])} {e(v['kw'])}, 이렇게 비교하세요</h2><div class="guide"><p>{e(v['intro'][0])}</p><p>{e(v['intro'][1])}</p><p class="pt"><strong>{e(d['name'])} 현장 포인트.</strong> {e(hook)}</p></div></section>
<section class="sec"><h2>자주 묻는 질문</h2>{faq_html}</section>
<section class="sec"><h2>{GN} 다른 동 {e(v['kw'])}</h2><div class="chips">{others_d}</div></section>'''
    crumbs = [(GN, '/'), (d['name'], dong_path(d)), (v['kw'], None)]
    jsonld = [
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":f"{GN} 청소업체","item":HOST+'/'},
            {"@type":"ListItem","position":2,"name":d['name'],"item":HOST+dong_path(d)},
            {"@type":"ListItem","position":3,"name":f"{d['name']} {v['kw']}","item":HOST+path}]},
        {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q, a in v['faq']]},
        {"@context":"https://schema.org","@type":"Service","name":f"{d['name']} {v['kw']} 비교견적","serviceType":v['kw'],
         "areaServed":{"@type":"Place","name":f"서울특별시 {GN} {d['name']}"},"description":desc,
         "provider":[{"@type":"LocalBusiness","name":c['name'],"telephone":c['tel'],"url":c['home']} for c in COMPANIES]}]
    og = HOST + pub(pick[0]) if pick else None
    write(path, layout(title, desc, path, body, crumbs, jsonld, og))
    return path, title, desc

# ───────── 허브 페이지 ─────────
def vert_hub(v):
    path = vert_path(v)
    title = f"{GN} {v['kw']} 업체 비교 · 법정동 {len(DONGS)}곳 견적 안내"
    desc = f"{GN} 전 지역 {v['kw']} 업체 3곳 비교. {v['desc']} {GU["sample"]} 등 동별 안내 페이지로 이동."
    ph = photo_list(v)[:6]
    items = [(page_path(DONGS[i % len(DONGS)], v), pub(p), f'{v["kw"]} 작업 {i+1}', f'서울 {GN} · {v["kw"]}') for i, p in enumerate(ph)]
    chips = ''.join(f'<a href="{page_path(d, v)}">{e(d["name"])}</a>' for d in DONGS)
    tiles = ''.join(f'<div class="tile"><i>{"✅🧹🕐📋"[i]}</i><small>작업 포인트 {i+1}</small>{e(p)}</div>' for i, p in enumerate(v['points']))
    body = f'''<div class="hero"><div class="k">서울 {GN}</div><h1>{GN} <em>{e(v['kw'])}</em>,<br>동을 고르면 바로 비교</h1><p>{e(v['intro'][0])}</p></div>
<section class="sec"><h2>동별 {e(v['kw'])}</h2><p class="sub">법정동 {len(DONGS)}곳</p><div class="chips">{chips}</div></section>
{company_rows(None, v)}
{feed(items, f'{GN} {v["kw"]} 작업 사례', '실제 현장 사진입니다')}
<section class="sec"><h2>{e(v['kw'])} 안심 포인트</h2><div class="tiles">{tiles}</div></section>
<section class="sec"><h2>견적 포인트</h2><div class="guide"><p>{e(v['intro'][1])}</p></div></section>'''
    crumbs = [(GN, '/'), (v['kw'], None)]
    jsonld = [{"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":HOST+path}]
    write(path, layout(title, desc, path, body, crumbs, jsonld, og_for(v)))
    return path, title, desc

def dong_hub(d):
    path = dong_path(d)
    title = f"{d['name']} 청소업체 비교 · 업종 19종 견적 안내"
    desc = f"{d['name']} 청소업체 3곳 비교. {d['name']}은 {d['trait']}. 사무실·병원·학원·입주·준공 등 업종별 {d['name']} 청소 안내."
    body = f'''<div class="hero"><div class="k">서울 {GN}</div><h1><em>{e(d['name'])}</em>에서<br>어떤 청소가 필요하세요?</h1><p>{e(d['name'])}은 {e(d['trait'])}입니다. 업종을 고르면 작업 방식과 업체 3곳 연락처가 바로 나옵니다.</p></div>
<section class="sec"><h2>{e(d['name'])} 청소 종류</h2><p class="sub">업종 19종</p>{icon_grid(d)}</section>
{company_rows(None, None)}'''
    crumbs = [(GN, '/'), (d['name'], None)]
    jsonld = [{"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":HOST+path}]
    write(path, layout(title, desc, path, body, crumbs, jsonld))
    return path, title, desc

def root():
    path = '/'
    title = f"{GN} 청소업체 비교 · 동별 · 업종별 견적 안내"
    desc = f"서울 {GN} 법정동 {len(DONGS)}곳 × 청소 업종 19종. 행진크린·지니크린·청소뱅크 3곳을 한 화면에서 비교하고 전화 또는 무료견적 폼으로 바로 문의."
    items = []
    for i, v in enumerate(VERTICALS[:6]):
        ph = photo_list(v)
        if ph: items.append((vert_path(v), pub(ph[0]), f'{GN} {v["kw"]}', f'서울 {GN} · {v["kw"]}'))
    chips = ''.join(f'<a href="{dong_path(d)}">{e(d["name"])}</a>' for d in DONGS)
    body = f'''<div class="hero"><div class="k">서울 {GN}</div><h1>{GN}에서<br><em>어떤 청소</em>가 필요하세요?</h1><p>업종과 동을 고르면 작업 방식과 업체 3곳 연락처가 바로 나옵니다. 견적은 각 업체에 직접 요청합니다.</p></div>
<section class="sec"><h2>청소 종류별</h2><p class="sub">업종 19종</p>{icon_grid()}</section>
<section class="sec"><h2>동별로 찾기</h2><p class="sub">법정동 {len(DONGS)}곳</p><div class="chips">{chips}</div></section>
{feed(items, '최근 {GN} 작업 사례', '실제 현장 사진입니다')}
{company_rows(None, None)}'''
    jsonld = [{"@context":"https://schema.org","@type":"WebSite","name":BRAND,"url":HOST+'/'}]
    write(path, layout(title, desc, path, body, [(GN, None)], jsonld))
    return path, title, desc

# ───────── 빌드 ─────────
def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ASSETS / 'logos', OUT / 'assets' / 'logos')
    for d in (ASSETS / 'svc').iterdir():
        if d.is_dir():
            for p in d.iterdir():
                if not p.name.startswith('.'):
                    dst = OUT / pub(p).lstrip('/'); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(p, dst)
    pages = [root()] + [vert_hub(v) for v in VERTICALS] + [dong_hub(d) for d in DONGS]
    pages += [dong_vert_page(d, v, di) for di, d in enumerate(DONGS) for v in VERTICALS]
    titles = [t for _, t, _ in pages]; descs = [s for _, _, s in pages]
    assert len(set(titles)) == len(titles), '제목 중복'
    assert len(set(descs)) == len(descs), '설명 중복'
    urls = ''.join(f'<url><loc>{e(HOST + p)}</loc></url>' for p, _, _ in pages)
    (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {HOST}/sitemap.xml\n', encoding='utf-8')
    (OUT / f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY, encoding='utf-8')
    (OUT / '404.html').write_text(layout('페이지를 찾을 수 없습니다', f'{GN} 청소업체 비교', '/404.html',
        '<div class="hero"><h1>페이지가 없습니다</h1><p>주소가 바뀌었거나 없는 페이지입니다.</p><div class="cta"><a class="btn p" href="/">홈으로</a></div></div>', [(GN, '/')], [], bar=False), encoding='utf-8')
    for f in (OUT.parent / 'verify' / GU_SLUG).glob('naver*.html'): shutil.copy(f, OUT / f.name)  # 네이버 서치어드바이저 소유확인 파일 (구별)
    (OUT / '_headers').write_text('/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n', encoding='utf-8')
    json.dump([p for p, _, _ in pages], open(OUT.parent / f'urls_{GU_SLUG}.json', 'w'), ensure_ascii=False, indent=0)
    print(f'pages={len(pages)} files={sum(1 for _ in OUT.rglob("*") if _.is_file())} host={HOST}')

if __name__ == '__main__':
    build()
