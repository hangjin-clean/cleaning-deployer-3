import os
import gen as g
from national_regions import REGIONS

MAX_ALLOWED=8000
LIMIT=max(1,min(int(os.getenv("BULK_LIMIT","100")),MAX_ALLOWED))
KEYS=["office","hospital","academy","store","restaurant","school","gym","factory","salon","stairs","cafe","daycare","bath","movein","completion","exterior","flood","fire","aircon"]

def title5(r,k,label):
    s,f=r["title_short"],r["title_full"]
    x={
    "hospital":[f"{s} 병원청소 업체추천",f"{f} 병원청소 업체추천",f"{s} 병원정기청소 전문업체",f"{f} 병원정기청소 전문업체",f"{f} 병원청소업체 비용안내"],
    "office":[f"{s} 사무실청소 업체추천",f"{f} 사무실 정기청소 업체",f"{s} 사무실청소 전문업체",f"{f} 사무실청소업체 비용안내",f"{f} 사무실 정기관리 청소업체"],
    "academy":[f"{s} 학원청소 업체추천",f"{f} 학원 정기청소 업체",f"{s} 학원청소 전문업체",f"{f} 학원청소업체 비용안내",f"{f} 교습소 스터디카페 청소업체"],
    "stairs":[f"{s} 계단청소 업체추천",f"{f} 계단청소 정기관리 업체",f"{s} 빌라 계단청소 전문업체",f"{f} 계단청소업체 비용안내",f"{f} 상가 건물 계단청소 업체"]}
    return x.get(k,[f"{s} {label} 업체추천",f"{f} {label} 전문업체",f"{s} {label} 비용안내",f"{f} {label} 정기관리",f"{f} {label} 업체추천"])

def make(r,v,k,n,title):
    path=f'/published/national/{r["slug"]}/{k}/v{n}/'
    full=r["display_full"]
    body=('<div class="hero"><div class="k">'+g.e(full)+'</div><h1>'+g.e(title)+'</h1>'
          '<p>'+g.e(r["title_full"])+'에서 필요한 '+g.e(v["kw"])+' 정보를 확인하고, 청소 종류와 업체 3곳의 연락처를 한 화면에서 비교할 수 있습니다. 견적은 각 업체에 직접 요청합니다.</p></div>'
          '<section class="sec"><h2>청소 종류별</h2><p class="sub">업종 19종</p>'+g.icon_grid()+'</section>'+g.company_rows(None,None))
    desc=f'{title}. {full} {v["kw"]} 안내와 청소업체 비교 및 견적 안내.'
    js=[{"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":g.HOST+path}]
    g.write(path,g.layout(title,desc,path,body,[(r["title_full"],None)],js,g.og_for(v)))

def main():
    made=0
    for r in REGIONS:
      for i,v in enumerate(g.VERTICALS[:19]):
       k=KEYS[i]
       for n,t in enumerate(title5(r,k,v["kw"]),1):
        if made>=LIMIT:
         print(f"[3호 전국] {made}개 생성 완료 / LIMIT={LIMIT}"); return
        make(r,v,k,n,t); made+=1
    print(f"[3호 전국] {made}개 생성 완료")
if __name__=="__main__": main()
