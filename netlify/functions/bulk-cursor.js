const {json,auth,blobStore}=require('./_shared');
exports.handler=async function(event){
 if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
const s=await blobStore('cleaning3-bulk-state');
 if(event.httpMethod==='GET'){
   const d=await s.get('cursor',{type:'json'})||{cursor:0,updatedAt:null};return json(200,d);
 }
 if(event.httpMethod==='POST'){
   let p={};try{p=JSON.parse(event.body||'{}')}catch(e){}
   const cursor=Math.max(0,Math.floor(Number(p.cursor)||0));
   const d={cursor,updatedAt:new Date().toISOString()};await s.setJSON('cursor',d);return json(200,d);
 }
 return json(405,{error:'method not allowed'});
};
