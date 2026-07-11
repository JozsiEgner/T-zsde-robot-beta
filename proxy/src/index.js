const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };

function corsHeaders(origin, allowedOrigin) {
  const allowed = allowedOrigin || "*";
  return {
    "access-control-allow-origin": allowed === "*" ? "*" : (origin === allowed ? origin : allowed),
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type,authorization,x-proxy-token",
    "access-control-max-age": "86400",
  };
}

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...JSON_HEADERS, ...extraHeaders },
  });
}

function isAuthorized(request, env) {
  if (!env.PROXY_TOKEN) return false;
  const supplied = request.headers.get("x-proxy-token") || "";
  return supplied === env.PROXY_TOKEN;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request.headers.get("origin"), env.ALLOWED_ORIGIN);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (url.pathname === "/health") {
      return json({ ok: true, service: "trading-api-proxy" }, 200, cors);
    }

    if (!isAuthorized(request, env)) {
      return json({ error: "unauthorized" }, 401, cors);
    }

    if (url.pathname === "/market/ticker" && request.method === "GET") {
      const symbol = (url.searchParams.get("symbol") || "BTCUSDT").toUpperCase();
      if (!/^[A-Z0-9]{5,20}$/.test(symbol)) {
        return json({ error: "invalid_symbol" }, 400, cors);
      }

      const upstream = `https://api.binance.com/api/v3/ticker/bookTicker?symbol=${encodeURIComponent(symbol)}`;
      const response = await fetch(upstream, { headers: { accept: "application/json" } });
      const body = await response.text();
      return new Response(body, {
        status: response.status,
        headers: { ...cors, "content-type": response.headers.get("content-type") || "application/json" },
      });
    }

    return json({ error: "not_found" }, 404, cors);
  },
};
