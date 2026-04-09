"""
Multi-wallet distributor: send native token from one source to a group.
Supports SOL and ETH/EVM, randomized amounts, random delays, and retry.
"""
from typing import Optional
from .utils import setup_logging, random_delay, random_amount, retry

_log = setup_logging()


def send_native_multi(
    from_private_key: str,
    recipients: list[dict],
    amount: float,
    chain: str,
    rpc_url: Optional[str] = None,
    randomize: bool = False,
    delay_min: int = 1,
    delay_max: int = 30,
    retry_attempts: int = 3,
) -> dict:
    """
    Send native token from one source wallet to all recipients.

    Args:
        from_private_key: private key of sender (base58 for Solana, hex for EVM)
        recipients:       list of wallet dicts (must each have 'address')
        amount:           base amount per wallet (SOL or ETH)
        chain:            'solana' or 'evm'
        rpc_url:          custom RPC (falls back to env/default)
        randomize:        if True, randomize each send ±10%
        delay_min/max:    seconds to sleep between sends
        retry_attempts:   retry count per failed send

    Returns:
        {status, chain, total, sent, failed, results}
    """
    chain = chain.lower()
    if chain == "solana":
        from .solana import send_sol, DEFAULT_RPC
        send_fn, default_rpc = send_sol, DEFAULT_RPC
    elif chain == "evm":
        from .evm import send_eth, DEFAULT_RPC
        send_fn, default_rpc = send_eth, DEFAULT_RPC
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    rpc     = rpc_url or default_rpc
    results = []
    sent    = 0
    failed  = 0

    for i, wallet in enumerate(recipients):
        to_addr   = wallet["address"]
        send_amt  = random_amount(amount) if randomize else amount

        def _do(addr=to_addr, amt=send_amt):
            return send_fn(from_private_key, addr, amt, rpc)

        try:
            tx_hash = retry(_do, attempts=retry_attempts, delay=5)
            results.append({"address": to_addr, "amount": send_amt, "tx_hash": tx_hash, "status": "sent"})
            sent += 1
            _log.info(f"[{i+1}/{len(recipients)}] {send_amt} {chain} → {to_addr} | {tx_hash}")
        except Exception as e:
            results.append({"address": to_addr, "amount": send_amt, "tx_hash": None, "status": "failed", "error": str(e)})
            failed += 1
            _log.error(f"[{i+1}/{len(recipients)}] Failed → {to_addr}: {e}")

        if i < len(recipients) - 1:
            random_delay(delay_min, delay_max)

    return {
        "status":  "success" if failed == 0 else "partial",
        "chain":   chain,
        "total":   len(recipients),
        "sent":    sent,
        "failed":  failed,
        "results": results,
    }
