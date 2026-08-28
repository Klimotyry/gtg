from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Config:
    bot_token: str
    support_url: str
    channel_url: str
    buy_rate: float
    sell_rate: float
    buy_reserve_bc: int
    sell_reserve_rub: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add a fresh token.")

    return Config(
        bot_token=token,
        support_url=os.getenv("SUPPORT_URL", "https://t.me/your_support").strip(),
        channel_url=os.getenv("CHANNEL_URL", "https://t.me/your_channel").strip(),
        buy_rate=_float("BUY_RATE_RUB_PER_1000", 1.2),
        sell_rate=_float("SELL_RATE_RUB_PER_1000", 0.85),
        buy_reserve_bc=_int("BUY_RESERVE_BC", 10_492_339),
        sell_reserve_rub=_int("SELL_RESERVE_RUB", 99_214),
    )
