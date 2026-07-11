# Trading API Proxy

Cloudflare Worker alapú, minimális piaci adatproxy.

## Végpontok

- `GET /health`
- `GET /market/ticker?symbol=BTCUSDT`

A ticker végpont `x-proxy-token` fejlécet kér.

## Titok beállítása

```powershell
cd proxy
npm install
npx wrangler secret put PROXY_TOKEN
```

A titkos token nem kerül a GitHub-repóba.

## Fejlesztői indítás

```powershell
npm run dev
```

## Telepítés

```powershell
npm run deploy
```

## CORS

A `wrangler.toml` fájlban az `ALLOWED_ORIGIN` értékét éles használat előtt állítsd a saját weboldalad pontos originjére, például:

```toml
ALLOWED_ORIGIN = "https://example.com"
```

## Példa kérés

```javascript
fetch("https://YOUR-WORKER.workers.dev/market/ticker?symbol=BTCUSDT", {
  headers: {
    "x-proxy-token": "A_WORKER_SECRETBEN_BEÁLLÍTOTT_TOKEN"
  }
});
```

Ez a béta proxy csak publikus ticker-adatot továbbít. Kereskedési API-kulcsok továbbítására még nincs engedélyezve.
