# Ézó Trading Robot — biztonságos kezdőverzió

Ez a projekt egy konfigurálható, alapértelmezetten **paper-trading** kriptotőzsdei robot.

## Fő logika

A döntés nem egyetlen indikátorból születik. A robot több, egymástól részben független jelet súlyoz:

- trend: gyors és lassú EMA
- momentum: RSI
- árpozíció: Bollinger-sáv
- volatilitási pajzs: ATR
- forgalmi megerősítés
- 0-Roulette döntés: BUY / HOLD / SELL közül a legmagasabb pontszám
- Árnyék-kulcs: csak megfelelő bizalmi szintnél enged pozíciót
- Arbitrációs pajzs: extrém spread, volatilitás vagy veszteség esetén tilt

## Biztonság

- `PAPER_MODE=true` az alapérték.
- Valódi kereskedéshez külön át kell írni `PAPER_MODE=false` értékre.
- API-kulcshoz csak kereskedési jogosultságot adj; kiutalási jogot ne.
- Először legalább több hét paper-trading és backtest szükséges.
- Nincs garantált hozam.

## Telepítés Windows alatt

```powershell
cd "A_KICSOMAGOLT_MAPPA"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
py main.py
```

## Binance Spot Testnet

A `.env` fájlban:

```env
EXCHANGE=binance
SANDBOX_MODE=true
PAPER_MODE=true
```

A CCXT-ben a sandbox módot közvetlenül az exchange példány létrehozása után kell bekapcsolni.

## Élő mód előtti kötelező ellenőrzés

1. Legalább 500 lezárt paper ügylet.
2. Pozitív eredmény több eltérő piaci időszakban.
3. Maximum drawdown elfogadható tartományban.
4. API-kulcs kiutalás nélkül.
5. Kis összegű, kézi felügyeletű indulás.
