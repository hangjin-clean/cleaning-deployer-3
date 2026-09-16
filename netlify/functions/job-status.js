const {json,auth,blobStore}=require('./_shared');
exports.handler=async function(event){
 if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
 const id=(event.queryStringParameters||{}).id;
 if(!id)return json(400,{error:'job id가 없습니다.'});
 try{
const store=await blobStore('cleaning3-generation-jobs');
   const data=await store.get(`jobs/${id}`,{type:'json',consistency:'strong'});
   if(!data)return json(404,{error:'작업을 찾을 수 없습니다.'});
   return json(200,data);
 }catch(e){
   return json(500,{error:'작업상태 조회 오류: '+(e.message||String(e))});
 }
};
