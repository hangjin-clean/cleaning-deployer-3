const {json,auth,blobStore}=require('./_shared');
exports.handler=async function(event){
 if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
 try{
const m=await blobStore('cleaning3-publish-manifests');
   const latest=await m.get('latest',{type:'json'});
   const urls=(latest&&latest.urls)||[];if(!urls.length)throw new Error('공개 URL이 없습니다.');
   const sample=even(urls,Math.min(10,urls.length));
   const checks=await Promise.all(sample.map(async u=>{
     try{const r=await fetch(u+'?audit='+Date.now(),{redirect:'follow',headers:{'Cache-Control':'no-cache'}});const t=await r.text();return {url:u,ok:r.ok&&/청소배포 3호/.test(t)&&/<title>/.test(t),status:r.status}}catch(e){return {url:u,ok:false,error:e.message}}
   }));
   return json(200,{pass:checks.every(x=>x.ok),total:urls.length,sample:checks});
 }catch(e){return json(500,{error:e.message})}
};
function even(a,n){if(a.length<=n)return a;const o=[];for(let i=0;i<n;i++)o.push(a[Math.round(i*(a.length-1)/(n-1))]);return [...new Set(o)]}
