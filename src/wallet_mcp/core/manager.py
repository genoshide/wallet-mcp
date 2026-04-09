"""
Wallet manager: list wallets, batch balance checks, tagging, group summaries.
"""
from typing import Optional
from .utils import setup_logging

_log = setup_logging()


def list_wallets(
    chain:     Optional[str] = None,
    label:     Optional[str] = None,
    tag:       Optional[str] = None,
    show_keys: bool = False,
) -> list[dict]:
    """Return wallets with optional filter. Private keys masked unless show_keys=True."""
    from .storage import filter_wallets
    wallets = filter_wallets(chain=chain, label=label, tag=tag)
    if not show_keys:
        for w in wallets:
            pk = w.get("private_key", "")
            w["private_key"] = (pk[:6] + "…" + pk[-4:]) if len(pk) > 10 else "***"
    return wallets


def get_balance_batch(
    chain:   Optional[str] = None,
    label:   Optional[str] = None,
    tag:     Optional[str] = None,
    rpc_url: Optional[str] = None,
) -> dict:
    """Fetch native balances for all wallets matching the filter."""
    from .storage import filter_wallets
    wallets = filter_wallets(chain=chain, label=label, tag=tag)

    if not wallets:
        return {"total": 0, "sum": 0.0, "results": []}

    evm_wallets = [w for w in wallets if w["chain"].lower() == "evm"]
    sol_wallets = [w for w in wallets if w["chain"].lower() == "solana"]
    results: list[dict] = []

    if evm_wallets:
        from .evm import get_evm_balances_batch, DEFAULT_RPC
        evm_addrs = [wallet["address"] for wallet in evm_wallets]
        for wallet, r in zip(evm_wallets, get_evm_balances_batch(evm_addrs, rpc_url or DEFAULT_RPC)):
            results.append({**r, "chain": "evm", "label": wallet["label"]})

    if sol_wallets:
        from .solana import get_sol_balances_batch, DEFAULT_RPC
        sol_addrs = [wallet["address"] for wallet in sol_wallets]
        for wallet, r in zip(sol_wallets, get_sol_balances_batch(sol_addrs, rpc_url or DEFAULT_RPC)):
            results.append({**r, "chain": "solana", "label": wallet["label"]})

    total_sum = sum(r["balance"] for r in results if r.get("balance") is not None)
    return {"total": len(results), "sum": round(total_sum, 9), "results": results}


def group_summary() -> list[dict]:
    """Return wallet count summary grouped by label and chain."""
    from .storage import load_wallets
    from collections import defaultdict
    groups: dict[str, dict] = defaultdict(lambda: {"evm": 0, "solana": 0, "total": 0})
    for w in load_wallets():
        key = w["label"]
        c   = w["chain"].lower()
        groups[key][c]       = groups[key].get(c, 0) + 1
        groups[key]["total"] += 1
    return [{"label": k, **v} for k, v in groups.items()]


def tag_label(label: str, tag: str) -> dict:
    from .storage import tag_wallets
    updated = tag_wallets(label, tag)
    return {"label": label, "tag": tag, "updated": updated}


def delete_group(label: str) -> dict:
    from .storage import delete_wallets_by_label
    removed = delete_wallets_by_label(label)
    return {"label": label, "deleted": removed}
