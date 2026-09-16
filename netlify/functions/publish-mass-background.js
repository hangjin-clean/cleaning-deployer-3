const {auth,blobStore}=require('./_shared');

exports.handler=async function(event){
 if(!auth(event)){console.log('Unauthorized publish');return}
 let p={};try{p=JSON.parse(event.body||'{}')}catch(e){return}
 const {publishId,jobIds}=p;
 if(!publishId||!Array.isArray(jobIds)||!jobIds.length)return;
const jobs=await blobStore('cleaning3-generation-jobs');
 const pages=await blobStore('cleaning3-published-pages');
 const status=await blobStore('cleaning3-bulk-publish');
 const manifests=await blobStore('cleaning3-publish-manifests');

 let state={id:publishId,status:'collecting',phase:'collecting',total:0,processed:0,failed:0,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()};
 const save=async()=>{state.updatedAt=new Date().toISOString();await status.setJSON(`publish/${publishId}`,state)};
 try{
   const existing=await status.get(`publish/${publishId}`,{type:'json'});
   if(existing&&['collecting','publishing','completed','indexnow'].includes(existing.status))return;
   await save();
   const all=[],seen=new Set();
   for(const id of jobIds){
     const job=await jobs.get(`jobs/${id}`,{type:'json'});
     if(!job)continue;
     for(const it of(job.items||[])){
       if(it.status!=='completed'||!it.page)continue;
       const k=it.page.urlPath||it.page.canonical||it.page.title;
       if(seen.has(k))continue;seen.add(k);all.push(it.page);
     }
   }
   if(!all.length)throw new Error('배포할 완료 페이지가 없습니다.');
   state.total=all.length;state.status='publishing';state.phase='blobs';await save();
   const chunk=Math.min(100,Math.max(10,Number(process.env.PUBLISH_CHUNK_SIZE||50)));
   for(let i=0;i<all.length;i+=chunk){
     const part=all.slice(i,i+chunk);
     await Promise.all(part.map(pg=>pages.setJSON(`page/${encodeURIComponent(pg.urlPath)}`,pg)));
     state.processed=Math.min(i+part.length,all.length);await save();
   }
   const urls=all.map(x=>x.canonical).filter(Boolean);
   const manifest={id:publishId,count:all.length,urls,paths:all.map(x=>x.urlPath),createdAt:new Date().toISOString()};
   await manifests.setJSON(`manifest/${publishId}`,manifest);
   await manifests.setJSON('latest',manifest);
   state.status='completed';state.phase='completed';state.finishedAt=new Date().toISOString();await save();
 }catch(e){
   state.status='failed';state.phase='failed';state.error=e.message;state.finishedAt=new Date().toISOString();await save();
 }
};
