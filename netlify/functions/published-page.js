const {esc,blobStore,buildPage}=require('./_shared');
const services=require('../../data/services.json');

const PROVINCE_BY_SHORT={
  '서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시',
  '광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시',
  '경기':'경기도','강원':'강원특별자치도','충북':'충청북도','충남':'충청남도',
  '전북':'전북특별자치도','전남':'전라남도','경북':'경상북도','경남':'경상남도',
  '제주':'제주특별자치도'
};

const ICONS=['🏢','🏥','📚','🛍️','🍽️','🏫','🏋️','🏭','💇','🪜','☕','🧸','🛁','🚚','🏗️','🧗','🌊','🔥','❄️'];
exports.handler=async function(event){
  try{
    const raw=(event.queryStringParameters||{}).path||'';
    const clean=String(raw).replace(/^\/+/,'');
    const path='/published/'+clean.replace(/^published\//,'');
    const pages=await blobStore('cleaning3-published-pages');

    let p=await getPage(pages,path);
    if(!p)p=rebuildFromPath(path);
    if(!p)return simple(404,'페이지를 찾을 수 없습니다.');
    return {
      statusCode:200,
      headers:{
        'Content-Type':'text/html; charset=utf-8',
        'Cache-Control':'public, max-age=300'
      },
      body:html(p)
    };
  }catch(e){
    return simple(500,'페이지 로딩 오류: '+(e.message||String(e)));
  }
};
async function getPage(pages,path){
  const candidates=new Set([path]);
  try{candidates.add(decodeURIComponent(path))}catch(e){}
  try{candidates.add(encodeURI(decodeURIComponent(path)))}catch(e){}
  for(const candidate of candidates){
    try{
      const p=await pages.get(`page/${encodeURIComponent(candidate)}`,{type:'json'});
      if(p)return p;
    }catch(e){}
  }
  return null;
}
function rebuildFromPath(path){
  try{
    const decoded=decodeURIComponent(path);
    const parts=decoded.split('/').filter(Boolean);
    if(parts[0]!=='published')return null;
    if(parts.length!==5 && parts.length!==6)return null;

    const provinceShort=parts[1];
    const district=parts[2];
    const hasDong=parts.length===6;
    const dong=hasDong?parts[3]:'';
    const serviceSlug=hasDong?parts[4]:parts[3];
    const versionPart=hasDong?parts[5]:parts[4];
    const service=services.find(x=>x.slug===serviceSlug);
    if(!service)return null;

    const m=/^v([1-5])-/.exec(versionPart);
    if(!m)return null;
    const variant=Number(m[1])-1;

    const region=PROVINCE_BY_SHORT[provinceShort]||provinceShort;
    const p=buildPage({region,district,dong,serviceId:service.id,variant});
    const site=String(process.env.SITE_URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
    p.urlPath=decoded;
    p.canonical=site+decoded;
    return p;
  }catch(e){
    return null;
  }
}
function html(p){
  const area=String(p.area||p.dong||p.district||'').trim();
  const district=String(p.district||'').trim();
  const region=String(p.region||'').trim();
  const serviceName=String(p.serviceName||p.keyword||'청소').trim();
  const place=area||district;
  const regionLabel=[region,district,area].filter((x,i,a)=>x&&a.indexOf(x)===i).join(' ');
  const serviceTiles=services.slice(0,19).map((s,i)=>{
    const name=esc(s.name||s.coreKeyword||'청소');
    return `<div class="tile"><div class="ico">${ICONS[i]||'🧹'}</div><div>${name}</div></div>`;
  }).join('');
  return `<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(p.title||`${place} ${serviceName} 업체 비교`)}</title>
<meta name="description" content="${esc(p.description||`${place} ${serviceName} 업체 비교 안내`)}">
<meta name="robots" content="index,follow"><link rel="canonical" href="${esc(p.canonical||'')}">
<style>${CSS}</style></head><body>
<header class="top"><div class="wrap topin"><a class="brand" href="/">청소비용비교</a><a class="btn p" href="#compare">견적받기</a></div></header>
<main class="wrap">
  <div class="crumb">${esc(place||district)}</div>
  <section class="hero">
    <div class="k">${esc(regionLabel)}</div>
    <h1>${esc(place||district)}에서<br><em>${esc(serviceName)}</em>가 필요하세요?</h1>
    <p>${esc(place||district)} ${esc(serviceName)} 작업 방식과 업체 조건을 한 화면에서 비교하세요. 견적은 각 업체에 직접 요청할 수 있습니다.</p>
  </section>
  <section class="sec">
    <h2>청소 종류별</h2><p class="sub">업종 19종</p><div class="grid">${serviceTiles}</div>
  </section>
  <section class="sec">
    <h2>${esc(place||district)} ${esc(serviceName)} 안내</h2>
    <div class="panel text"><h3>${esc(p.title||`${place} ${serviceName}`)}</h3>
    <p>${esc(p.intro||`${place} 지역 ${serviceName} 작업 범위와 관리 조건을 비교해보세요.`)}</p>
    <p>${esc(p.work||'작업 범위, 일정, 정기관리 여부와 비용 조건을 확인한 뒤 원하는 업체를 선택할 수 있습니다.')}</p></div>
  </section>
  <section class="sec" id="compare">
    <h2>청소업체 비교</h2><p class="sub">지역과 업종에 맞는 업체 조건을 확인하세요.</p>
    <div class="panel">
      <div class="company"><div><b>행진크린</b><span>법인·기업 사업장 전문 · 하청 없이 직접</span></div><a href="tel:01033007431">전화 상담</a></div>
      <div class="company"><div><b>지니크린</b><span>개인 사업장 맞춤 청소 · 직접 관리</span></div><a href="tel:01059261764">전화 상담</a></div>
      <div class="company"><div><b>청소뱅크</b><span>개인 사업장·병원 정기관리 · 무료 방문견적</span></div><a href="tel:01068560158">전화 상담</a></div>
    </div>
  </section>
  <section class="sec"><h2>견적 확인 포인트</h2><div class="panel text"><p>작업 범위, 방문 주기, 추가 비용 기준, 결제 조건을 함께 비교하면 업체 선택이 쉬워집니다.</p></div></section>
</main>
<div class="bottom"><a class="btn o" href="tel:01033007431">☎ 전화 상담</a><a class="btn p" href="#compare">무료 견적 받기</a></div>
</body></html>`;
}
const CSS=`
:root{--p:#4B4DFF;--p2:#6C6EFF;--pl:#EEF0FF;--bg:#F5F6FA;--card:#fff;--tx:#1B1D2A;--mu:#6B7280;--bd:#E9EBF2}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,Inter,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.6;padding-bottom:92px}
a{color:inherit;text-decoration:none}.wrap{max-width:780px;margin:0 auto;padding:0 16px}
.top{position:sticky;top:0;z-index:20;background:#fff;border-bottom:1px solid var(--bd)}.topin{height:64px;display:flex;align-items:center;justify-content:space-between}
.brand{font-weight:900;font-size:23px;color:var(--p);font-style:italic;letter-spacing:-1px}.btn{display:inline-flex;align-items:center;justify-content:center;padding:11px 17px;border-radius:12px;font-weight:800;font-size:14px;border:1px solid transparent}.btn.p{background:var(--p);color:#fff}.btn.o{background:#fff;border-color:var(--bd)}
.crumb{font-size:12px;color:var(--mu);padding:14px 0 0}.hero{background:#fff;border:1px solid var(--bd);border-radius:20px;padding:28px 22px;margin:16px 0}.hero .k{font-size:13px;color:var(--p);font-weight:800}.hero h1{font-size:30px;line-height:1.3;margin:7px 0 12px;letter-spacing:-1.2px}.hero h1 em{font-style:normal;color:var(--p)}.hero p{margin:0;color:var(--mu);font-size:15px}
.sec{margin:28px 0}.sec h2{font-size:20px;margin:0 0 4px}.sub{font-size:13px;color:var(--mu);margin:0 0 14px}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}.tile{background:#fff;border:1px solid var(--bd);border-radius:14px;min-height:88px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:12px;font-weight:700;text-align:center}.ico{font-size:24px;margin-bottom:7px}
.panel{background:#fff;border:1px solid var(--bd);border-radius:18px;overflow:hidden}.text{padding:20px}.text h3{margin:0 0 10px;font-size:18px}.text p{color:var(--mu);margin:8px 0;font-size:14px}.company{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:17px 18px;border-top:1px solid var(--bd)}.company:first-child{border-top:0}.company b{display:block;font-size:16px}.company span{display:block;font-size:12px;color:var(--mu);margin-top:3px}.company a{background:var(--pl);color:var(--p);padding:9px 12px;border-radius:10px;font-size:12px;font-weight:800;white-space:nowrap}
.bottom{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--bd);padding:10px 16px;display:flex;gap:8px;justify-content:center;z-index:30}.bottom .btn{width:min(370px,50%)}
@media(max-width:640px){.grid{grid-template-columns:repeat(3,1fr)}.hero h1{font-size:27px}.company{align-items:flex-start}.company span{max-width:190px}}
`;
function simple(statusCode,msg){return {statusCode,headers:{'Content-Type':'text/html; charset=utf-8'},body:`<!doctype html><meta charset="utf-8"><h1>${esc(msg)}</h1>`}}
