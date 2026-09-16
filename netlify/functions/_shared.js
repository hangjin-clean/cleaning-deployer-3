const services=require('../../data/services.json');

function json(statusCode,data){
 return {statusCode,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'},body:JSON.stringify(data)};
}
function auth(event){
 const expected=String(process.env.ADMIN_KEY||'').trim();
 if(!expected)return true;
 const got=String(event?.headers?.['x-admin-key']||event?.headers?.['X-Admin-Key']||'').trim();
 return got===expected;
}
function slug(s=''){
 return encodeURIComponent(String(s).trim().replace(/\s+/g,'-'));
}
function esc(s=''){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function serviceById(id){return services.find(x=>x.id===id)||services[0]}
function hash(s=''){let h=2166136261;for(const c of String(s)){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return (h>>>0).toString(36)}
function shortProvince(x=''){
 const m={'서울특별시':'서울','부산광역시':'부산','대구광역시':'대구','인천광역시':'인천','광주광역시':'광주',
 '대전광역시':'대전','울산광역시':'울산','세종특별자치시':'세종','경기도':'경기','강원특별자치도':'강원',
 '충청북도':'충북','충청남도':'충남','전북특별자치도':'전북','전라남도':'전남','경상북도':'경북','경상남도':'경남'};
 return m[x]||x;
}
function buildPage(input){
 const service=serviceById(input.serviceId);
 const variant=Math.max(0,Number(input.variant||0))%5;
 const keyword=String(service.coreKeyword||service.name||'').trim();
 const province=String(input.region||'').trim();
 const district=String(input.district||'').trim();
 const dong=String(input.dong||'').trim();
 const pshort=shortProvince(province);

 // 핵심키워드는 제목마다 정확히 1회 중심에 두고, 5개 패턴만 순환합니다.
 // "업체 업체", "청소 청소" 같은 기계적 중복을 피합니다.
 const suffixes=[
   '전문업체 비교',
   '홈클리닝 업체 추천',
   '비용 견적 비교',
   '우리동네 청소업체',
   '무료견적 업체 비교'
 ];
 const titlePatterns=[
   `${dong} ${keyword} ${district} ${suffixes[0]}`,
   `${district} ${dong} ${keyword} ${suffixes[1]}`,
   `${dong} ${keyword} ${pshort} ${district} ${suffixes[2]}`,
   `${dong} ${keyword} ${suffixes[3]}`,
   `${district} ${dong} ${keyword} ${suffixes[4]}`
 ];
 const title=titlePatterns[variant].replace(/\s+/g,' ').trim();
 const subs=(service.subkeywords||[]).slice(0,7);
 const intro=`${province} ${district} ${dong}에서 ${keyword} 서비스를 알아볼 때는 가격만 확인하기보다 작업 범위, 일정, 추가 비용 기준과 업체 조건을 함께 비교하는 것이 좋습니다. 현장 상태와 필요한 작업 범위에 따라 견적은 달라질 수 있습니다. 청소배포 3호는 간단한 정보를 입력하면 조건에 맞는 청소업체를 비교할 수 있도록 구성한 청소 견적 비교 플랫폼입니다.`;
 const relatedText=subs.length?` 함께 비교해볼 관련 항목은 ${subs.join(', ')} 등이 있습니다.`:'';
 const work=`${keyword} 상담 시에는 필요한 작업 범위를 먼저 정리해 두면 비교가 쉬워집니다.${relatedText} 업체별 포함·제외 작업, 예상 소요시간, 결제 조건 등을 확인한 뒤 원하는 조건에 맞는 곳을 선택하세요. 청소배포 3호는 무조건 가장 저렴한 곳보다 가격·작업범위·결제조건·업체 신뢰도를 함께 비교할 수 있도록 돕습니다.`;
 const path=`/published/${slug(pshort)}/${slug(district)}/${slug(dong)}/${service.slug}/v${variant+1}-${hash(province+'|'+district+'|'+dong+'|'+service.id+'|'+variant)}`;
 const site=String(process.env.SITE_URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
 return {
   id:hash(path),region:province,district,area:dong,dong,
   category:service.category||'홈클리닝',serviceId:service.id,serviceName:service.name,serviceSlug:service.slug,
   variant,keyword,title,
   description:`${district} ${dong} ${keyword} 비교. 우리동네에서 가까운 곳 우선, 3개 청소업체 비교.`,
   intro,work,subkeywords:subs,
   urlPath:path,canonical:site+path,
   generatedAt:new Date().toISOString()
 };
}
async function blobStore(name){
 const siteID=String(process.env.BLOBS_SITE_ID||process.env.NETLIFY_SITE_ID||'').trim();
 const token=String(process.env.BLOBS_TOKEN||process.env.NETLIFY_TOKEN||'').trim();
 if(!siteID||!token){
   throw new Error('Netlify Blobs 환경변수(BLOBS_SITE_ID, BLOBS_TOKEN)가 없습니다.');
 }
 const {getStore}=await import('@netlify/blobs');
 return getStore({name,consistency:'strong',siteID,token});
}

module.exports={json,auth,slug,esc,serviceById,buildPage,shortProvince,hash,blobStore};
