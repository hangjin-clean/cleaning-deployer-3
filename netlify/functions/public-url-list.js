const {json,auth,blobStore}=require('./_shared');

exports.handler=async function(event){
 if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
 try{
   const manifests=await blobStore('cleaning3-publish-manifests');
   const listed=await manifests.list({prefix:'manifest/'});
   const blobs=(listed.blobs||[]).slice().sort((a,b)=>String(b.key).localeCompare(String(a.key)));
   const urls=[];
   for(const b of blobs){
     const m=await manifests.get(b.key,{type:'json'});
     if(m&&Array.isArray(m.urls)){
       for(const u of m.urls)if(u&&!urls.includes(u))urls.push(u);
     }
     if(urls.length>=10)break;
   }
   const origin=String(process.env.URL||'https://cleaning-compare-3.netlify.app').replace(/\/$/,'');
   return json(200,{total:urls.length,urls:urls.slice(0,10).map(u=>/^https?:\/\//i.test(u)?u:origin+(u.startsWith('/')?'':'/')+u)});
 }catch(e){return json(500,{error:e.message||String(e)})}
};
