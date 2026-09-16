export default async (req) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ok:false,error:"POST only"}),{status:405});
  try{
    const body = await req.json();
    const count = Math.max(1, Math.min(10000, Number(body.count||100)));
    const token = Netlify.env.get("GITHUB_TOKEN");
    const owner = Netlify.env.get("GITHUB_OWNER") || "hangjin-clean";
    const repo = Netlify.env.get("GITHUB_REPO") || "cleaning3-deployer";
    const branch = Netlify.env.get("GITHUB_BRANCH") || "main";
    if(!token) return new Response(JSON.stringify({ok:false,error:"GITHUB_TOKEN 환경변수가 없습니다."}),{status:500});

    const api=`https://api.github.com/repos/${owner}/${repo}/contents/deploy-config.json`;
    const headers={"Authorization":`Bearer ${token}`,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"};
    let sha;
    const cur=await fetch(api+"?ref="+encodeURIComponent(branch),{headers});
    if(cur.ok){ const j=await cur.json(); sha=j.sha; }

    const content = JSON.stringify({count,seed:String(Date.now()),generatedAt:new Date().toISOString()},null,2);
    const payload={message:`2호 대량배포: ${count} pages`,content:btoa(unescape(encodeURIComponent(content))),branch};
    if(sha) payload.sha=sha;
    const r=await fetch(api,{method:"PUT",headers,body:JSON.stringify(payload)});
    const j=await r.json();
    if(!r.ok) throw new Error(j.message||"GitHub commit failed");
    return new Response(JSON.stringify({ok:true,message:`${count.toLocaleString()}페이지 설정 커밋 완료. Netlify 자동 빌드가 시작됩니다.`}),{headers:{"content-type":"application/json"}});
  }catch(e){
    return new Response(JSON.stringify({ok:false,error:e.message}),{status:500,headers:{"content-type":"application/json"}});
  }
}
