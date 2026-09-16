const {esc,blobStore,buildPage}=require('./_shared');
const services=require('../../data/services.json');

const PROVINCE_BY_SHORT={
  '서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시',
  '광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시',
  '경기':'경기도','강원':'강원특별자치도','충북':'충청북도','충남':'충청남도',
  '전북':'전북특별자치도','전남':'전라남도','경북':'경상북도','경남':'경상남도'
};

exports.handler=async function(event){
  try{
    const raw=(event.queryStringParameters||{}).path||'';
    const path='/' + String(raw).replace(/^\/+/,'');
    const pages=await blobStore('cleaning3-published-pages');

    let p=await getPage(pages,path);
    if(!p){
      p=rebuildFromPath(path);
    }

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
    if(parts.length<6 || parts[0]!=='published')return null;

    const provinceShort=parts[1];
    const district=parts[2];
    const dong=parts[3];
    const serviceSlug=parts[4];
    const versionPart=parts[5];

    const service=services.find(x=>x.slug===serviceSlug);
    if(!service)return null;

    const m=/^v([1-5])-/.exec(versionPart);
    if(!m)return null;
    const variant=Number(m[1])-1;

    const region=PROVINCE_BY_SHORT[provinceShort]||provinceShort;
    const p=buildPage({
      region,
      district,
      dong,
      serviceId:service.id,
      variant
    });

    const site=String(process.env.SITE_URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
    p.urlPath=decoded;
    p.canonical=site+decoded;
    return p;
  }catch(e){
    return null;
  }
}

function html(p){
  const reviews=[
    ['★★★★★',`${p.serviceName} / 경기 수원시`,'신축아파트 입주 전이라 여러 업체 조건을 한 번에 비교할 수 있어서 편했어요. 상담도 빠르고 원하는 날짜에 맞춰 진행할 수 있어서 준비가 훨씬 수월했습니다.','김*진'],
    ['★★★★★','이사청소 / 서울 송파구','이사 날짜가 촉박했는데 여러 곳을 따로 찾지 않아도 되어 편했습니다. 견적과 작업범위를 비교하고 일정에 맞는 업체를 선택할 수 있었어요.','박*영'],
    ['★★★★★','사업장청소 / 경기 성남시','비용뿐 아니라 작업범위와 결제조건을 같이 비교할 수 있어서 원하는 조건에 맞는 곳을 찾기 좋았습니다.','이*호']
  ];

  const reviewImgs=['/review-kitchen.jpg','/review-bath.jpg','/review-room.jpg'];

  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(p.title)}</title><meta name="description" content="${esc(p.description)}"><meta name="robots" content="index,follow"><link rel="canonical" href="${esc(p.canonical)}">
<style>${CSS}</style></head><body>

<header class="top">
  <div class="topin">
    <img class="brandlogo" src="/cleaning3-logo.png.png" alt="청소배포 3호">
    <div class="tagline">필요한 일, 청소배포 3호에서 한 번에</div>
    <div class="platform">청소 견적 비교 플랫폼</div>
  </div>
</header>

<section class="hero">
  <div class="heroOverlay"></div>
  <div class="wrap heroInner">
    <div class="heroText">
      <div class="eyebrow">CLEAN LIFE · BETTER TOMORROW</div>
      <h1>청소가 필요할 땐,<br><strong>청소배포 3호에서</strong></h1>
      <div class="sub">간단한 정보만 입력하고<br>검증된 청소업체의 견적을 최대 5곳까지 비교하세요.</div>
      <div class="location">● ${esc(p.district)} ${esc(p.area)} · ${esc(p.keyword||p.serviceName)}</div>
    </div>
  </div>
</section>

<section class="benefits">
  <div class="wrap chips">
    <div class="benefit"><div class="bicon blue">▣</div><b>회원가입 없음</b><span>간편하게 바로 신청</span></div>
    <div class="benefit"><div class="bicon green">⚡</div><b>30초 신청</b><span>빠른 견적 요청</span></div>
    <div class="benefit"><div class="bicon orange">₩</div><b>무료 견적</b><span>비용 부담 없이</span></div>
    <div class="benefit"><div class="bicon purple">●●</div><b>최대 5곳 비교</b><span>여러 업체 한 번에</span></div>
    <div class="benefit"><div class="bicon pink">✓</div><b>검증 업체 우선</b><span>믿을 수 있는 업체</span></div>
  </div>
</section>

<section class="quotearea">
  <div class="wrap quote">
    <div class="quoteLead">
      <div class="mini">간단한 정보로 빠르게 시작하세요!</div>
      <h2>무료 견적 신청</h2>
      <p>필요한 정보만 간단하게 입력해주세요.</p>
    </div>
    <div class="quoteAction">
      <div class="quoteinfo">${esc(p.area)} 지역과 <b>${esc(p.keyword||p.serviceName)}</b> 등 필요한 정보를 간단하게 입력하면<br><strong>최대 5곳의 청소 견적을 비교</strong>할 수 있습니다.</div>
      <a class="cta" href="https://forms.gle/kNoQu5FJc2wDoC2t6">무료 견적 신청하기 ›</a>
      <div class="safe"><span>🔒 개인정보 안전보호</span><span>◷ 빠른 업체 매칭</span><span>♡ 무료 비교견적</span></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 class="title"><strong>청소배포 3호</strong>가 선택받는 이유</h2>
    <div class="reasonGrid">
      <div class="reason"><div class="ricon">✓</div><h3>검증된 청소업체</h3><p>기본적인 사업자 정보와 서비스 조건을 확인한 업체를 우선 연결합니다.</p></div>
      <div class="reason"><div class="ricon">₩</div><h3>합리적인 비용</h3><p>여러 업체의 견적과 작업 조건을 비교해 원하는 조건을 선택할 수 있습니다.</p></div>
      <div class="reason"><div class="ricon">◷</div><h3>빠른 견적 & 매칭</h3><p>지역과 청소 정보를 입력하고 필요한 업체의 견적을 편리하게 비교하세요.</p></div>
      <div class="reason"><div class="ricon">♡</div><h3>다양한 청소 서비스</h3><p>입주·이사·거주청소 등 지역별 필요한 청소 서비스를 비교할 수 있습니다.</p></div>
    </div>
  </div>
</section>

<section class="section how">
  <div class="wrap">
    <h2 class="title">청소배포 3호는 이렇게 이용해요</h2>
    <div class="grid3">
      <div class="step"><div class="num">1</div><h3>정보 입력</h3><p>지역과 청소 종류 등 필요한 정보만 간단하게 입력합니다.</p></div>
      <div class="step"><div class="num">2</div><h3>견적 받기</h3><p>조건에 맞는 청소업체의 견적을 최대 5곳까지 받아봅니다.</p></div>
      <div class="step"><div class="num">3</div><h3>비교 후 선택</h3><p>가격과 일정, 작업범위를 비교하고 원하는 업체를 선택합니다.</p></div>
    </div>
  </div>
</section>

<section class="section reviews">
  <div class="wrap">
    <h2 class="title">실제 이용 고객 후기</h2>
    <p class="sectiondesc">청소배포 3호를 통해 견적을 받은 고객들의 생생한 후기입니다.</p>
    <div class="grid3">
      ${reviews.map((r,i)=>`
        <div class="review">
          <img src="${reviewImgs[i]}" alt="청소 후기 이미지" class="reviewImg">
          <div class="stars">${r[0]}</div>
          <h3>${esc(r[1])}</h3>
          <p>${esc(r[2])}</p>
          <div class="reviewer">${esc(r[3])}</div>
        </div>
      `).join('')}
    </div>
  </div>
</section>

<section class="section alt">
  <div class="wrap guide">
    <div>
      <h2 class="title">${esc(p.area)} ${esc(p.serviceName)} 안내</h2>
      <div class="content"><p>${esc(p.intro)}</p><p>${esc(p.work)}</p></div>
    </div>
    <div class="seo">${(p.subkeywords||[]).map(x=>`<span>${esc(x)}</span>`).join('')}</div>
  </div>
</section>

<section class="dark">
  <div class="wrap">
    <div class="darkTop">
      <div>
        <h2 class="title">아무 업체나 연결하지 않습니다.</h2>
        <p class="lead">청소배포 3호는 단순 연결에서 끝나는 플랫폼이 아니라,<br>고객이 안심하고 맡길 수 있는 조건을 갖춘 업체를 우선 연결합니다.</p>
      </div>
      <div class="grid4">
        <div class="trust"><div class="icon">✓</div><h3>영업배상책임보험 가입 업체</h3></div>
        <div class="trust"><div class="icon">▣</div><h3>사업자 정보 확인</h3></div>
        <div class="trust"><div class="icon">▤</div><h3>세금계산서 발급 가능</h3></div>
        <div class="trust"><div class="icon">♡</div><h3>검증 업체 우선</h3></div>
      </div>
    </div>
    <div class="bluebox">
      <div><div class="finalsmall">견적만 연결하고 끝? 청소배포 3호는 다릅니다.</div><h3>청소가 필요할 땐, 청소배포 3호에서</h3><p>간단하게 신청하고 최대 5곳의 청소 견적을 비교해보세요.</p></div>
      <a class="whitebtn" href="https://forms.gle/kNoQu5FJc2wDoC2t6">무료 견적 신청하기 ›</a>
    </div>
  </div>
</section>
</body></html>`;
}

const CSS=`
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:Arial,"Noto Sans KR","Apple SD Gothic Neo",sans-serif;color:#10213d;background:#f5f9ff;line-height:1.65;word-break:keep-all;overflow-wrap:break-word}
a{text-decoration:none;color:inherit}.wrap{width:min(1120px,calc(100% - 40px));margin:0 auto}
.top{height:72px;background:#fff;border-bottom:1px solid #e5edf7;display:flex;align-items:center;position:relative;z-index:3}
.topin{width:min(1120px,calc(100% - 40px));margin:auto;display:flex;align-items:center;gap:18px}
.brandlogo{width:72px;height:48px;object-fit:contain}.tagline{font-size:15px;font-weight:700;color:#31445f}.platform{margin-left:auto;background:#eaf4ff;color:#1264dd;padding:9px 16px;border-radius:999px;font-weight:700;font-size:14px}
.hero{position:relative;min-height:360px;background:url('/hero-livingroom.jpg') center/cover no-repeat;display:flex;align-items:center}
.heroOverlay{position:absolute;inset:0;background:linear-gradient(90deg,rgba(246,251,255,.97) 0%,rgba(246,251,255,.83) 42%,rgba(246,251,255,.18) 72%,rgba(246,251,255,0) 100%)}
.heroInner{position:relative;z-index:1}.heroText{max-width:560px;padding:54px 0}
.eyebrow{font-size:13px;color:#2574e8;letter-spacing:1.5px;font-weight:700;margin-bottom:10px}
.hero h1{font-size:56px;line-height:1.14;letter-spacing:-2.6px;margin:0 0 18px;color:#07162d}.hero h1 strong{color:#1267e8}
.sub{font-size:20px;line-height:1.65;color:#41536c}.location{display:inline-block;margin-top:18px;background:#fff;padding:9px 15px;border-radius:999px;color:#16417b;font-weight:700;box-shadow:0 6px 18px rgba(20,78,150,.08)}
.benefits{margin-top:-26px;position:relative;z-index:2}.chips{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.benefit{background:#fff;border-radius:20px;padding:18px 10px;text-align:center;box-shadow:0 10px 28px rgba(20,74,138,.09)}
.bicon{width:46px;height:46px;border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px}.blue{background:#e5f1ff;color:#1473ed}.green{background:#e2f9ef;color:#13a66b}.orange{background:#fff0df;color:#ff8b19}.purple{background:#f0e8ff;color:#8753e8}.pink{background:#ffe7ef;color:#ef4778}
.benefit b{display:block;font-size:16px}.benefit span{display:block;font-size:12px;color:#708095;margin-top:3px}
.quotearea{padding:28px 0 45px}.quote{background:#fff;border-radius:24px;padding:28px 34px;box-shadow:0 12px 36px rgba(25,73,140,.10);display:grid;grid-template-columns:1fr 1.6fr;gap:34px;align-items:center}
.mini{font-size:12px;color:#1670ec;font-weight:800;margin-bottom:6px}.quote h2{font-size:34px;margin:0 0 4px}.quote p{margin:0;color:#6f7f93}.quoteinfo{background:#edf6ff;padding:17px;border-radius:16px;text-align:center;color:#41536c}
.cta{display:block;margin-top:12px;background:linear-gradient(90deg,#1773ee,#2f66ea);color:#fff;text-align:center;padding:16px;border-radius:13px;font-size:20px;font-weight:800;box-shadow:0 10px 24px rgba(28,99,225,.20)}
.safe{display:flex;justify-content:center;gap:26px;font-size:11px;color:#6f7f93;margin-top:11px}
.section{padding:48px 0;background:#f7fbff}.section.alt{background:#fff}.title{font-size:30px;line-height:1.3;letter-spacing:-1px;margin:0 0 20px}.title strong{color:#1267e8}.sectiondesc{margin-top:-10px;color:#758397}
.reasonGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.reason,.step,.review{background:#fff;border-radius:18px;padding:22px;box-shadow:0 8px 24px rgba(24,71,133,.07)}.ricon{width:42px;height:42px;border-radius:50%;background:#e8f2ff;color:#1670ee;display:flex;align-items:center;justify-content:center;font-weight:900;margin-bottom:10px}
.reason h3,.step h3,.review h3{margin:0 0 7px;font-size:17px}.reason p,.step p{margin:0;color:#6f8093;font-size:13px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.step .num{width:38px;height:38px;border-radius:50%;background:#176fee;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;margin-bottom:12px}
.reviews{background:#eef6ff}.review{padding:12px 12px 18px}.reviewImg{width:100%;height:135px;object-fit:cover;border-radius:13px;margin-bottom:10px}.stars{color:#ff9d00;font-size:16px}.review p{font-size:13px;color:#40536c}.reviewer{font-size:12px;color:#76869a;margin-top:10px}
.guide{display:grid;grid-template-columns:2fr 1fr;gap:30px;align-items:center}.content{background:#f7faff;border:1px solid #e6eef8;border-radius:18px;padding:20px;color:#40536d}.seo{display:flex;flex-wrap:wrap;gap:8px}.seo span{background:#eaf3ff;color:#2861a7;padding:7px 10px;border-radius:999px;font-size:12px}
.dark{background:#0c1a32;color:#fff;padding:34px 0}.darkTop{display:grid;grid-template-columns:1.1fr 2fr;gap:24px;align-items:center}.dark .title{color:#fff}.lead{color:#c5d1e2;font-size:14px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.trust{background:#fff;color:#13223a;border-radius:16px;padding:16px;text-align:center}.trust .icon{color:#176fee;font-size:21px;margin-bottom:6px}.trust h3{font-size:13px;margin:0}
.bluebox{margin-top:18px;background:linear-gradient(90deg,#1260d2,#2f70f0);border-radius:18px;padding:18px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}.bluebox h3{font-size:24px;margin:2px 0}.bluebox p{margin:0;color:#e8f1ff;font-size:13px}.finalsmall{font-size:11px;opacity:.9}.whitebtn{background:#fff;color:#1265df;font-weight:800;padding:14px 22px;border-radius:14px;white-space:nowrap}

@media(max-width:800px){
  .wrap,.topin{width:calc(100% - 28px)}
  .top{height:64px}.brandlogo{width:58px;height:42px}.tagline{display:none}.platform{font-size:11px;padding:7px 10px}
  .hero{min-height:0;background-position:68% center}.heroOverlay{background:linear-gradient(180deg,rgba(246,251,255,.96) 0%,rgba(246,251,255,.90) 58%,rgba(246,251,255,.72) 100%)}.heroText{padding:42px 0 120px;max-width:none;text-align:center}
  .hero h1{font-size:38px;line-height:1.2;letter-spacing:-1.6px}.sub{font-size:16px}.location{font-size:13px}
  .benefits{margin-top:-88px}.chips{grid-template-columns:repeat(2,1fr);gap:9px}.benefit:last-child{grid-column:1/-1}.benefit{padding:14px 8px}.benefit b{font-size:14px}.benefit span{font-size:11px}
  .quote{grid-template-columns:1fr;gap:16px;padding:22px 16px}.quote h2{font-size:27px}.quoteLead{text-align:center}.quoteinfo{font-size:14px;line-height:1.75}.cta{font-size:18px;padding:15px}.safe{gap:8px;justify-content:space-between;flex-wrap:wrap}
  .section{padding:38px 0}.title{font-size:26px}.reasonGrid,.grid3,.grid4,.guide,.darkTop{grid-template-columns:1fr}.reviewImg{height:170px}
  .bluebox{display:block;text-align:center}.whitebtn{display:block;margin-top:14px;width:100%}
  .lead br{display:none}
}

@media(max-width:420px){
  .hero h1{font-size:34px}.sub{font-size:15px}.quote h2,.title{font-size:24px}.reviewImg{height:150px}
}
`;

function simple(statusCode,msg){return {statusCode,headers:{'Content-Type':'text/html; charset=utf-8'},body:`<!doctype html><meta charset="utf-8"><h1>${esc(msg)}</h1>`}}
