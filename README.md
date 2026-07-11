# Ézó Trading Robot — beta

Ez a projekt egy konfigurálható, alapértelmezetten **paper-trading** tőzsdei robot. A technikai jelréteg mellett opcionális XAU fundamentális fair-value és anomáliaérzékelő modult is tartalmaz.

## Fő logika

- trend: gyors és lassú EMA
- momentum: RSI
- árpozíció: Bollinger-sáv
- volatilitási pajzs: ATR
- forgalmi megerősítés
- 0-Roulette döntés: BUY / HOLD / SELL
- Árnyék-kulcs: minimális bizalmi szint
- Arbitrációs pajzs: spread-, volatilitás- és veszteséglimit

## XAU fundamentális modell

Az `xau_model.py` külön rétegként számolja:

- DXY-változás hatását
- reálhozam-változás hatását
- geopolitikai kockázatot
- központi banki és ETF-flow-t
- fizikai kereslet-kínálati egyensúlyt
- cost-of-carry fair value-t
- spot/futures basis eltérést
- fundamentális és piaci vektor divergenciaszögét
- standardizált reziduális eltérést

A kimenet nem állít bizonyított manipulációt. A rendszer a következő kockázati állapotokat adja:

- `ALLOW`: normál vagy megfelelően megerősített mozgás
- `REDUCE`: fundamentális divergencia; csökkentett pozícióméret
- `BLOCK`: magas anomáliakockázat; új pozíció tiltása

A modell bekapcsolása:

```env
ENABLE_XAU_MODEL=true
```

A fundamentális bemeneteket `-1..+1` tartományban kell megadni. A `RESIDUAL_*` és `BASIS_*` értékeket történeti adatokból kell kalibrálni. Kalibrálatlan, `1` szórásértékkel a modul csak fejlesztési demonstráció.

## Cost-of-carry

A futures fair value:

```text
F* = S0 × exp((r + u - y) × T)
```

ahol `T` a kontraktus lejáratáig hátralévő ismert idő, nem garantált korrekciós időpont.

## Biztonság

- `PAPER_MODE=true` az alapérték.
- `SANDBOX_MODE=true` az alapérték.
- API-kulcshoz kiutalási jogosultságot ne adj.
- Az `.env` fájlt a `.gitignore` kizárja.
- A modell nem garantál profitot és nem bizonyít piaci manipulációt.

## Telepítés Windows alatt

```powershell
cd "A_KICSOMAGOLT_MAPPA"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
py main.py
```

Vagy indítsd a `start_robot.bat` fájlt.

## Tesztek

```powershell
py -m unittest test_xau_model.py
py -m compileall .
```

## Élő mód előtti kötelező ellenőrzés

1. Legalább 500 lezárt paper ügylet.
2. Több eltérő piaci rezsimen végzett backtest.
3. Maximum drawdown és veszteséglimit ellenőrzése.
4. XAU reziduális és basis statisztikák történeti kalibrálása.
5. Adatforrás-frissesség és hibakezelés.
6. Kis összegű, kézi felügyeletű indulás.
