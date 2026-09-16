const {auth,buildPage,blobStore}=require('./_shared');

exports.handler=async function(event){
 let payload={}; let store=null; let job=null;
 try{
   if(!auth(event))throw new Error('관리자 인증 실패');
   try{payload=JSON.parse(event.body||'{}')}catch(e){throw new Error('요청 데이터 JSON 오류')}
   const {jobId,region,targets,serviceId}=payload;
   if(!jobId||!region||!Array.isArray(targets)||!targets.length||!serviceId)throw new Error('생성 요청 필수값이 없습니다.');
store=await blobStore('cleaning3-generation-jobs');
   job={
     id:jobId,status:'running',region,serviceId,total:targets.length,completed:0,failed:0,
     createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),
     items:targets.map(t=>({target:t,status:'queued'}))
   };
   const save=async()=>{job.updatedAt=new Date().toISOString();await store.setJSON(`jobs/${jobId}`,job)};
   await save();

   // 페이지 생성 자체는 네트워크/AI 호출이 없으므로 한 작업 안에서 안전하게 순차 처리합니다.
   // 작은 배치(기본 20)라 속도 차이는 거의 없고 상태 저장 충돌을 막습니다.
   for(let i=0;i<targets.length;i++){
     const t=targets[i],item=job.items[i];
     item.status='generating';await save();
     try{
       const page=buildPage({region,district:t.district,dong:t.dong,serviceId,variant:t.variant});
       item.page=page;item.status='completed';job.completed++;
     }catch(e){
       item.status='failed';item.error=e.message||String(e);job.failed++;
     }
     await save();
   }

   job.status=job.failed===job.total?'failed':'completed';
   job.finishedAt=new Date().toISOString();
   await save();
 }catch(e){
   console.log('CLEANING3_GENERATE_ERROR',e&&e.stack||e);
   try{
     if(store && payload.jobId){
       if(!job){
         job={id:payload.jobId,status:'failed',total:Array.isArray(payload.targets)?payload.targets.length:0,completed:0,failed:Array.isArray(payload.targets)?payload.targets.length:0,items:[],createdAt:new Date().toISOString()};
       }
       job.status='failed';job.error=e.message||String(e);job.finishedAt=new Date().toISOString();job.updatedAt=job.finishedAt;
       await store.setJSON(`jobs/${payload.jobId}`,job);
     }
   }catch(ignore){}
 }
};
