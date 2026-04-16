"""
Utility helpers: delays, amount randomization, retry logic, logging.
"""
import re
import random
import time
import logging
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(
    os.path.expanduser(os.getenv("WALLET_DATA_DIR", "~/.wallet-mcp")),
    "wallet-mcp.log",
)

# Solana private key: base58, 85-90 chars (64 bytes encoded). Addresses are ~44 chars — safe to distinguish.
# EVM private key: hex 64 chars (without 0x) or 66 chars (with 0x prefix).
_SOLANA_KEY_RE = re.compile(r'[1-9A-HJ-NP-Za-km-z]{85,90}')
_EVM_KEY_RE    = re.compile(r'(?:0x)?[0-9a-fA-F]{64}')


def _mask(key: str) -> str:
    """Return first 5 chars + *** + last 4 chars."""
    return key[:5] + "***" + key[-4:] if len(key) > 12 else "***"


class _KeyMaskingFilter(logging.Filter):
    """Redact Solana and EVM private keys from log messages."""
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            msg = _SOLANA_KEY_RE.sub(lambda m: _mask(m.group()), msg)
            msg = _EVM_KEY_RE.sub(lambda m: _mask(m.group()), msg)
            record.msg  = msg
            record.args = ()
        except Exception:
            pass
        return True


def setup_logging(level: str | None = None) -> logging.Logger:
    logger = logging.getLogger("wallet-mcp")
    if logger.handlers:
        return logger
    level_str = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, level_str.upper(), logging.INFO))
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    fh.addFilter(_KeyMaskingFilter())
    logger.addHandler(fh)
    return logger


def random_delay(min_sec: int = 1, max_sec: int = 30) -> None:
    """Sleep a random duration between min and max seconds."""
    delay = random.uniform(min_sec, max_sec)
    setup_logging().debug(f"Sleeping {delay:.2f}s")
    time.sleep(delay)


def random_amount(base: float, variance: float = 0.10) -> float:
    """Return base ± variance*base, rounded to 9 decimal places."""
    delta = base * variance
    return round(random.uniform(base - delta, base + delta), 9)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def retry(fn, attempts: int = 3, delay: int = 5):
    """Retry callable `fn` up to `attempts` times with fixed delay on failure."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last_exc: Exception | None = None
    log = setup_logging()
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            log.warning(f"Attempt {i + 1}/{attempts} failed: {exc}")
            if i < attempts - 1:
                time.sleep(delay)
    assert last_exc is not None
    raise last_exc
