from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    exchange: str = os.getenv("EXCHANGE", "binance")
    symbol: str = os.getenv("SYMBOL", "BTC/USDT")
    timeframe: str = os.getenv("TIMEFRAME", "5m")
    candle_limit: int = int(os.getenv("CANDLE_LIMIT", "250"))
    loop_seconds: int = int(os.getenv("LOOP_SECONDS", "30"))

    sandbox_mode: bool = env_bool("SANDBOX_MODE", True)
    paper_mode: bool = env_bool("PAPER_MODE", True)
    api_key: str = os.getenv("API_KEY", "")
    api_secret: str = os.getenv("API_SECRET", "")

    starting_cash: float = float(os.getenv("STARTING_CASH", "10000"))
    risk_per_trade: float = float(os.getenv("RISK_PER_TRADE", "0.005"))
    max_position_fraction: float = float(os.getenv("MAX_POSITION_FRACTION", "0.10"))
    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", "0.02"))
    max_spread_pct: float = float(os.getenv("MAX_SPREAD_PCT", "0.0025"))
    max_atr_pct: float = float(os.getenv("MAX_ATR_PCT", "0.035"))
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", "0.62"))
    stop_atr_multiplier: float = float(os.getenv("STOP_ATR_MULTIPLIER", "2.0"))
    take_profit_r: float = float(os.getenv("TAKE_PROFIT_R", "1.8"))
    fee_rate: float = float(os.getenv("FEE_RATE", "0.001"))

    enable_xau_model: bool = env_bool("ENABLE_XAU_MODEL", False)
    xau_forward_price: float = float(os.getenv("XAU_FORWARD_PRICE", "0"))
    xau_term_years: float = float(os.getenv("XAU_TERM_YEARS", "0.083333"))
    risk_free_rate: float = float(os.getenv("RISK_FREE_RATE", "0.04"))
    storage_rate: float = float(os.getenv("STORAGE_RATE", "0.003"))
    convenience_yield: float = float(os.getenv("CONVENIENCE_YIELD", "0.0"))
    residual_mean: float = float(os.getenv("RESIDUAL_MEAN", "0"))
    residual_std: float = float(os.getenv("RESIDUAL_STD", "1"))
    basis_mean: float = float(os.getenv("BASIS_MEAN", "0"))
    basis_std: float = float(os.getenv("BASIS_STD", "1"))

    dxy_change: float = float(os.getenv("DXY_CHANGE", "0"))
    real_yield_change: float = float(os.getenv("REAL_YIELD_CHANGE", "0"))
    geopolitical_risk: float = float(os.getenv("GEOPOLITICAL_RISK", "0"))
    central_bank_flow: float = float(os.getenv("CENTRAL_BANK_FLOW", "0"))
    etf_flow: float = float(os.getenv("ETF_FLOW", "0"))
    physical_balance: float = float(os.getenv("PHYSICAL_BALANCE", "0"))
