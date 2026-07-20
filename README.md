# Ézó Trading Robot — beta

Ez a projekt egy konfigurálható, alapértelmezetten **paper-trading** tőzsdei robot. A technikai jelréteg mellett opcionális XAU fundamentális fair-value és anomáliaérzékelő modult, valamint külön Civil Axis ország–termék–arany értékelő modult is tartalmaz.

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

## Civil Axis ország–termék–arany modell

A `civil_axis_model.py` a saját országonkénti értékelési logikát külön, tesztelhető Python-modulként valósítja meg.

A modell figyelembe veszi:

- az országhoz rendelt földrajzilag és gazdaságilag megfelelő referencia-terméket;
- az éves becsült termelést vagy fogást;
- a nemzetközi nagykereskedelmi árat;
- a világ népességére jutó termékértéket;
- az ország lakosságára jutó stratégiai tartalékértéket;
- a piaci kapitalizációt, forgalmat és nyitott kötésállományt;
- a termelési kapacitás súlyát;
- a szén-monoxid-kockázat környezeti büntetőszorzóját;
- a teljes föld feletti aranykészletből számított aranyérték/fő referenciát.

A kimenet egy aranyhoz viszonyított index és minősítés:

- `ARANY-SZINT FELETT`
- `ERŐS`
- `KÖZEPES`
- `GYENGE`

A `civil_axis_gate()` az indexet közvetlenül kereskedési kapuvá alakítja:

- `ALLOW`, pozíciószorzó `1.0`
- `REDUCE`, pozíciószorzó `0.5`
- `BLOCK`, pozíciószorzó `0.0`

Példa:

```python
from civil_axis_model import (
    CountryResourceInput,
    GoldReferenceInput,
    assess_country,
    civil_axis_gate,
)

gold = GoldReferenceInput(
    above_ground_quantity=216_000_000_000,
    spot_price=75,
    world_population=8_100_000_000,
)

country = CountryResourceInput(
    country="Kína",
    reference_product="tőkehal",
    annual_quantity=1_000_000_000,
    wholesale_price=4,
    country_population=1_410_000_000,
    strategic_reserve_value=2_000_000_000_000,
    market_cap=10_000_000_000_000,
    exchange_turnover=8_000_000_000_000,
    open_interest=1_000_000_000_000,
    production_capacity_score=1.0,
    co_risk=0.10,
)

assessment = assess_country(country, gold)
gate, multiplier = civil_axis_gate(assessment.gold_relative_index)
```

A példában szereplő adatok csak szemléltető értékek, nem hiteles piaci adatok.

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
- A Civil Axis bemeneti adatokat hiteles forrásból és azonos időpontra kell gyűjteni.

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
py -m unittest test_civil_axis_model.py
py -m compileall .
```

## Élő mód előtti kötelező ellenőrzés

1. Legalább 500 lezárt paper ügylet.
2. Több eltérő piaci rezsimen végzett backtest.
3. Maximum drawdown és veszteséglimit ellenőrzése.
4. XAU reziduális és basis statisztikák történeti kalibrálása.
5. Civil Axis bemenetek forrásának, mértékegységének és időbélyegének egységesítése.
6. Adatforrás-frissesség és hibakezelés.
7. Kis összegű, kézi felügyeletű indulás.
