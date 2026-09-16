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
  let dong=String(input.dong||'').trim();

  // 시·구·군이 동 자리에 중복 전달되면 제목/지역표기에서 한 번만 사용
  if(dong===district) dong='';
  const pshort=shortProvince(province);

  // 중구·동구·서구·남구·북구처럼 전국에 반복되는 구 이름은 광역지역을 함께 표시
  const ambiguousDistricts=new Set(['중구','동구','서구','남구','북구']);
  const displayDistrict=ambiguousDistricts.has(district)
    ? `${pshort} ${district}`.trim()
    : district;

  const subs=(service.subkeywords||[]).slice(0,7);

  const suffixes=[
    '전문업체 비교',
    '사업장청소 업체 추천',
    '비용 견적 비교',
    '우리동네 청소업체',
    '무료견적 업체 비교'
  ];

  // 제목 생성 전용 영역
  // 아래 영역만 업종별로 다양화하며, 배포/URL/Blobs/지역표시 로직은 건드리지 않는다.
  const titleSets={
    '사무실청소':[
      `${displayDistrict} 사무실청소 전문업체 비교`,
      `${displayDistrict} 사무실 정기청소 바닥청소`,
      `${displayDistrict} 사무실청소 업체 대청소 정기관리`,
      `${displayDistrict} 사무실청소 비용비교 바닥청소`,
      `${displayDistrict} 사무실 정기청소 대청소 바닥왁스코팅 비용`
    ],
    '병원청소':[
      `${displayDistrict} 병원청소 업체 추천`,
      `${displayDistrict} 병원청소 개인의원 마감청소`,
      `${displayDistrict} 병원 정기청소 업체 추천`,
      `${displayDistrict} 개인의원 오픈 마감청소`,
      `${displayDistrict} 병원청소 전문업체 비교`
    ],
    '학원청소':[
      `${displayDistrict} 학원청소 정기관리 업체`,
      `${displayDistrict} 학원청소 교습소 마감청소`,
      `${displayDistrict} 학원 정기청소 업체 추천`,
      `${displayDistrict} 공부방 학원청소 전문업체`,
      `${displayDistrict} 학원청소 전문업체 비교`
    ],
    '매장청소':[
      `${displayDistrict} 매장청소 마감청소 전문업체`,
      `${displayDistrict} 매장청소 사업장 정기관리`,
      `${displayDistrict} 매장청소 전문업체 비교`,
      `${displayDistrict} 매장 마감청소 업체 추천`,
      `${displayDistrict} 매장청소 정기관리 비용`
    ],
    '식당청소':[
      `${displayDistrict} 식당청소 마감청소 업체`,
      `${displayDistrict} 음식점 정기청소 주방청소`,
      `${displayDistrict} 식당청소 전문업체 비교`,
      `${displayDistrict} 식당 마감청소 정기관리`,
      `${displayDistrict} 음식점청소 주방 후드청소 업체`
    ],
    '학교청소':[
      `${displayDistrict} 학교청소 정기관리 업체`,
      `${displayDistrict} 학교청소 교실 화장실청소`,
      `${displayDistrict} 학교 대청소 전문업체`,
      `${displayDistrict} 학교청소 바닥청소 정기관리`,
      `${displayDistrict} 학교청소 전문업체 비교`
    ],
    '헬스장청소':[
      `${displayDistrict} 헬스장청소 정기관리 업체`,
      `${displayDistrict} 헬스장 마감청소 화장실청소`,
      `${displayDistrict} 헬스장청소 바닥청소 업체`,
      `${displayDistrict} 헬스장 정기청소 전문업체`,
      `${displayDistrict} 헬스장청소 업체 비교`
    ],
    '공장청소':[
      `${displayDistrict} 공장청소 전문업체 비교`,
      `${displayDistrict} 공장 정기청소 바닥청소`,
      `${displayDistrict} 공장청소 대청소 업체`,
      `${displayDistrict} 공장 바닥청소 정기관리`,
      `${displayDistrict} 공장청소 업체 비용 비교`
    ],
    '미용실청소':[
      `${displayDistrict} 미용실청소 마감청소 업체`,
      `${displayDistrict} 미용실 정기청소 바닥청소`,
      `${displayDistrict} 미용실청소 전문업체 비교`,
      `${displayDistrict} 미용실 마감청소 정기관리`,
      `${displayDistrict} 미용실청소 업체 추천`
    ],
    '계단청소':[
      `${displayDistrict} 계단청소 빌라 상가 업체`,
      `${displayDistrict} 계단 정기청소 건물청소`,
      `${displayDistrict} 계단청소 화장실 정기관리`,
      `${displayDistrict} 빌라 계단청소 전문업체`,
      `${displayDistrict} 계단청소 업체 비용 비교`
    ],
    '카페청소':[
      `${displayDistrict} 카페청소 마감청소 업체`,
      `${displayDistrict} 카페 정기청소 매장관리`,
      `${displayDistrict} 카페청소 전문업체 비교`,
      `${displayDistrict} 카페 마감청소 바닥청소`,
      `${displayDistrict} 베이커리 카페청소 업체 추천`
    ],
    '어린이집청소':[
      `${displayDistrict} 어린이집청소 정기관리 업체`,
      `${displayDistrict} 어린이집 소독 청소업체`,
      `${displayDistrict} 어린이집청소 화장실청소`,
      `${displayDistrict} 어린이집 대청소 전문업체`,
      `${displayDistrict} 어린이집청소 업체 비교`
    ],
    '목욕탕청소':[
      `${displayDistrict} 목욕탕청소 정기관리 업체`,
      `${displayDistrict} 목욕탕 사우나 마감청소`,
      `${displayDistrict} 목욕탕청소 전문업체 비교`,
      `${displayDistrict} 사우나청소 바닥청소 업체`,
      `${displayDistrict} 목욕탕 대청소 업체 추천`
    ],
    '입주청소':[
      `${displayDistrict} 입주청소 전문업체 비교`,
      `${displayDistrict} 아파트 입주청소 업체`,
      `${displayDistrict} 빌라 입주청소 비용 비교`,
      `${displayDistrict} 신축 입주청소 전문업체`,
      `${displayDistrict} 입주청소 업체 추천`
    ],
    '준공청소':[
      `${displayDistrict} 준공청소 전문업체 비교`,
      `${displayDistrict} 신축 준공청소 업체`,
      `${displayDistrict} 준공청소 바닥청소 대청소`,
      `${displayDistrict} 건물 준공청소 전문업체`,
      `${displayDistrict} 준공청소 업체 비용 비교`
    ],
    '외벽청소':[
      `${displayDistrict} 외벽청소 전문업체 비교`,
      `${displayDistrict} 건물 외벽청소 업체`,
      `${displayDistrict} 외벽 유리창청소 전문업체`,
      `${displayDistrict} 상가 외벽청소 업체 추천`,
      `${displayDistrict} 외벽청소 비용 견적 비교`
    ],
    '침수청소':[
      `${displayDistrict} 침수청소 전문업체`,
      `${displayDistrict} 침수 복구청소 업체`,
      `${displayDistrict} 물난리 침수청소 대청소`,
      `${displayDistrict} 침수청소 바닥청소 업체`,
      `${displayDistrict} 침수청소 업체 비용 비교`
    ],
    '화재청소':[
      `${displayDistrict} 화재청소 전문업체`,
      `${displayDistrict} 화재 복구청소 업체`,
      `${displayDistrict} 그을음청소 대청소 전문업체`,
      `${displayDistrict} 화재청소 냄새제거 업체`,
      `${displayDistrict} 화재청소 업체 비용 비교`
    ],
    '에어컨청소':[
      `${displayDistrict} 에어컨청소 전문업체 비교`,
      `${displayDistrict} 시스템에어컨 청소업체`,
      `${displayDistrict} 에어컨 분해청소 업체`,
      `${displayDistrict} 사업장 에어컨청소 전문업체`,
      `${displayDistrict} 에어컨청소 비용 비교`
    ]
  };

  const selectedTitles=titleSets[keyword]||[
    `${displayDistrict} ${keyword} 전문업체 비교`,
    `${displayDistrict} ${keyword} 정기관리 업체 추천`,
    `${displayDistrict} ${keyword} 비용 견적 비교`,
    `${displayDistrict} ${keyword} 전문 청소업체`,
    `${displayDistrict} ${keyword} 업체 비용 비교`
  ];
  const title=selectedTitles[variant].replace(/\s+/g,' ').trim();

  const intro=`${province} ${district} ${dong}에서 ${keyword} 서비스를 알아볼 때는 가격만 확인하기보다 작업 범위, 일정, 추가 비용 기준과 업체 조건을 함께 비교하는 것이 좋습니다. 현장 상태와 필요한 작업 범위에 따라 견적은 달라질 수 있습니다.`;
  const relatedText=subs.length?` 함께 비교해볼 관련 항목은 ${subs.join(', ')} 등이 있습니다.`:'';
  const work=`${keyword} 상담 시에는 필요한 작업 범위를 먼저 정리해 두면 비교가 쉬워집니다.${relatedText} 업체별 포함·제외 작업, 예상 소요시간, 결제 조건 등을 확인한 뒤 원하는 조건에 맞는 곳을 선택하세요. 청소배포 3호는 무조건 가장 저렴한 업체를 고르기보다 현장 조건에 맞는 업체를 비교할 수 있도록 안내합니다.`;
  const path=`/published/${slug(pshort)}/${slug(district)}/${slug(dong)}/${service.slug}/v${variant+1}-${hash(province+'|'+district+'|'+dong+'|'+service.id+'|'+variant)}`;
  const site=String(process.env.SITE_URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
  return {
    id:hash(path),region:province,district,area:dong,dong,
    category:service.category||'사업장청소',serviceId:service.id,serviceName:service.name,serviceSlug:service.slug,
    variant,keyword,title,
    description:`${displayDistrict} ${dong} ${keyword} 비교. 우리동네에서 가까운 곳 우선, 3개 청소업체 비교.`,
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

module.exports={services,json,auth,slug,esc,serviceById,hash,shortProvince,buildPage,blobStore};
