const {json,auth,blobStore}=require('./_shared');
exports.handler=async function(event){
 if(!auth(event))return json(401,{error:'관리자 인증이 필요합니다.'});
 const id=(event.queryStringParameters||{}).id;if(!id)return json(400,{error:'id가 없습니다.'});
const s=await blobStore('cleaning3-indexnow-status');
 const d=await s.get(`status/${id}`,{type:'json'});
 return d?json(200,d):json(404,{error:'IndexNow 작업을 찾을 수 없습니다.'});
};
