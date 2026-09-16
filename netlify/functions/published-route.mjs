import legacy from "./published-page.js";

export default async function handler(request) {
  try {
    const url = new URL(request.url);
    let path = decodeURIComponent(url.pathname);

    // 예전 /app/published/... 주소도 /published/...로 통일
    if (path.startsWith("/app/published/")) {
      path = path.slice(4);
    }

    const result = await legacy.handler({
      path,
      httpMethod: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      queryStringParameters: { path },
      body: null,
      isBase64Encoded: false
    });

    return new Response(result.body ?? "", {
      status: result.statusCode || 200,
      headers: result.headers || {
        "Content-Type": "text/html; charset=utf-8"
      }
    });
  } catch (error) {
    return new Response(
      `<!doctype html><meta charset="utf-8"><h1>페이지 로딩 오류: ${String(error?.message || error)}</h1>`,
      {
        status: 500,
        headers: { "Content-Type": "text/html; charset=utf-8" }
      }
    );
  }
}

export const config = {
  path: ["/published/*", "/app/published/*"]
};
