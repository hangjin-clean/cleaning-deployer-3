const {auth,blobStore}=require('./_shared');
const KEY=String(process.env.INDEXNOW_KEY||'').trim();
exports.handler=async function(event){
 if(!auth(event)){console.log('Unauthorized IndexNow');return}
 let p={};try{p=JSON.parse(event.body||'{}')}catch(e){return}
 const id=p.id||('idx-'+Date.now());
const manifests=await blobStore('cleaning3-publish-manifests');
 const status=await blobStore('cleaning3-indexnow-status');
 let st={id,status:'running',processed:0,total:0,batch:0,batches:0,failed:0,createdAt:new Date().toISOString()};
 const save=()=>status.setJSON(`status/${id}`,st);
 try{
   if(!KEY)throw new Error('INDEXNOW_KEY 환경변수가 없습니다.');
   const latest=await manifests.get('latest',{type:'json'});
   const urls=[...new Set((latest&&latest.urls)||[])];
   st.total=urls.length;st.batches=Math.ceil(urls.length/1000);await save();
   if(!urls.length)throw new Error('등록할 공개 URL이 없습니다.');
   const site=String(process.env.SITE_URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
   const host=new URL(site).host;
   for(let i=0;i<urls.length;i+=1000){
     const chunk=urls.slice(i,i+1000);
     const r=await fetch('https://searchadvisor.naver.com/indexnow',{method:'POST',headers:{'Content-Type':'application/json; charset=utf-8'},body:JSON.stringify({host,key:KEY,keyLocation:`${site}/${KEY}.txt`,urlList:chunk})});
     if(r.ok)st.processed+=chunk.length;else st.failed+=chunk.length;
     st.batch=Math.floor(i/1000)+1;await save();
   }
   st.status=st.failed?'failed':'completed';st.finishedAt=new Date().toISOString();await save();
 }catch(e){st.status='failed';st.error=e.message;st.finishedAt=new Date().toISOString();await save()}
};
