const {json,auth,blobStore}=require('./_shared');

exports.handler=async function(event){
  if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
  try{
    const manifests=await blobStore('cleaning3-publish-manifests');
    const latest=await manifests.get('latest',{type:'json'});
    const urls=(latest&&Array.isArray(latest.urls)?latest.urls:[]).filter(Boolean);
    if(!urls.length)throw new Error('공개 URL이 없습니다.');

    // 실제 공개된 URL 전체에서 최대 10개를 균등 선택
    const sample=even(urls,Math.min(10,urls.length));
    const checks=[];

    // 한꺼번에 10개를 self-fetch 하지 않고 순차 검증.
    // 일시적인 Netlify 429/5xx가 있으면 최대 3회 재시도한다.
    for(const url of sample){
      checks.push(await checkUrl(url));
    }

    const failed=checks.filter(x=>!x.ok);
    return json(200,{
      pass:failed.length===0,
      total:urls.length,
      checked:checks.length,
      failed:failed.length,
      sample:checks
    });
  }catch(e){
    return json(500,{error:e.message});
  }
};

async function checkUrl(url){
  let last={url,ok:false,status:0};
  for(let attempt=1;attempt<=3;attempt++){
    try{
      const r=await fetch(url,{
        redirect:'follow',
        headers:{
          'Cache-Control':'no-cache',
          'User-Agent':'cleaning-compare-3-verifier/1.0'
        }
      });
      const text=await r.text();
      const html=/<!doctype html/i.test(text)||/<html[\s>]/i.test(text)||/<title[\s>]/i.test(text);
      last={url,ok:r.ok&&html,status:r.status,attempt};
      if(last.ok)return last;

      // 404처럼 재시도해도 의미 없는 응답은 즉시 반환
      if(r.status>=400&&r.status<500&&r.status!==429)return last;
    }catch(e){
      last={url,ok:false,status:0,attempt,error:e.message};
    }
    await sleep(350*attempt);
  }
  return last;
}

function even(a,n){
  if(a.length<=n)return a;
  const out=[];
  for(let i=0;i<n;i++)out.push(a[Math.round(i*(a.length-1)/(n-1))]);
  return [...new Set(out)];
}

function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
