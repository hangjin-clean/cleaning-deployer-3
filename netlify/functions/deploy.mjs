export default async (request) => {
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
  };

  if (request.method === "OPTIONS") {
    return new Response("", { status: 204, headers });
  }

  if (request.method !== "POST") {
    return new Response(
      JSON.stringify({ ok: false, error: "POST 요청만 허용됩니다." }),
      { status: 405, headers }
    );
  }

  try {
    const body = await request.json().catch(() => ({}));

    const region = body.region || "all";
    const service = body.service || "all";
    const limit = Math.min(
      Math.max(Number(body.limit) || 100, 1),
      8000
    );

    const hookUrl = Netlify.env.get("BUILD_HOOK_URL");

    if (!hookUrl) {
      throw new Error("BUILD_HOOK_URL 환경변수가 설정되지 않았습니다.");
    }

    const response = await fetch(hookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) {
      throw new Error(`Build Hook 실행 실패: ${response.status}`);
    }

    return new Response(
      JSON.stringify({
        ok: true,
        message: "3호 배포 요청이 정상 접수되었습니다.",
        region,
        service,
        limit
      }),
      { status: 200, headers }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({
        ok: false,
        error: error.message
      }),
      { status: 500, headers }
    );
  }
};
