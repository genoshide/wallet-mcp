#!/usr/bin/env python3
"""
openclaw/wallet.py — Thin CLI wrapper for wallet-mcp.

Used by OpenClaw agents to call wallet-mcp functions directly
(no MCP protocol required; direct Python import).

Usage:
    python wallet.py <command> [--arg value ...]

Examples:
    python wallet.py generate_wallets --chain solana --count 10 --label airdrop1
    python wallet.py list_wallets --label airdrop1
    python wallet.py group_summary
    python wallet.py get_balance_batch --label airdrop1
    python wallet.py tag_wallets --label airdrop1 --tag funded
    python wallet.py delete_group --label airdrop1
    python wallet.py close_token_accounts --private-key 5Kd3...
    python wallet.py scan_token_accounts --address So1ana...
    python wallet.py send_native_multi --from-key 5Kd3... --label airdrop1 --amount 0.01 --chain solana
"""
import argparse
import json
import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env before importing wallet_mcp
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def _out(data: dict) -> None:
    print(json.dumps(data, indent=2))


def _err(msg: str) -> None:
    print(json.dumps({"status": "error", "message": msg}))
    sys.exit(1)


# ── Commands ──────────────────────────────────────────────────────────────

def cmd_generate_wallets(args):
    from wallet_mcp.core.generator import generate_wallets
    wallets = generate_wallets(
        chain=args.chain, count=args.count,
        label=args.label, tags=args.tags or ""
    )
    _out({"status": "success", "chain": args.chain,
          "label": args.label, "generated": len(wallets),
          "wallets": [{"address": w["address"]} for w in wallets]})


def cmd_send_native_multi(args):
    from wallet_mcp.core.storage import filter_wallets
    from wallet_mcp.core.distributor import send_native_multi
    recipients = filter_wallets(chain=args.chain, label=args.label,
                                tag=args.tag or None)
    if not recipients:
        _err(f"No wallets found for chain={args.chain} label={args.label}")
    _out(send_native_multi(
        from_private_key=args.from_key,
        recipients=recipients,
        amount=args.amount,
        chain=args.chain,
        rpc_url=args.rpc or None,
        randomize=args.randomize,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        retry_attempts=args.retries,
    ))


def cmd_list_wallets(args):
    from wallet_mcp.core.manager import list_wallets
    wallets = list_wallets(chain=args.chain or None, label=args.label or None,
                           tag=args.tag or None, show_keys=args.show_keys)
    _out({"status": "success", "count": len(wallets), "wallets": wallets})


def cmd_close_token_accounts(args):
    from wallet_mcp.core.solana import close_token_accounts
    result = close_token_accounts(private_key_b58=args.private_key,
                                  rpc_url=args.rpc or None,
                                  close_non_empty=args.close_non_empty)
    _out({"status": "success", **result})


def cmd_scan_token_accounts(args):
    from wallet_mcp.core.solana import get_token_accounts, DEFAULT_RPC
    accounts = get_token_accounts(args.address, args.rpc or DEFAULT_RPC)
    empty = [a for a in accounts if a["amount"] == 0]
    _out({"status": "success", "total": len(accounts),
          "empty": len(empty), "non_empty": len(accounts) - len(empty),
          "accounts": accounts})


def cmd_get_balance_batch(args):
    from wallet_mcp.core.manager import get_balance_batch
    result = get_balance_batch(chain=args.chain or None, label=args.label or None,
                               tag=args.tag or None, rpc_url=args.rpc or None)
    _out({"status": "success", **result})


def cmd_tag_wallets(args):
    from wallet_mcp.core.manager import tag_label
    _out({"status": "success", **tag_label(label=args.label, tag=args.tag)})


def cmd_group_summary(_args):
    from wallet_mcp.core.manager import group_summary
    _out({"status": "success", "groups": group_summary()})


def cmd_delete_group(args):
    from wallet_mcp.core.manager import delete_group
    _out({"status": "success", **delete_group(label=args.label)})


# ── Parser ────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(prog="wallet.py",
                                description="wallet-mcp CLI wrapper for OpenClaw")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # generate_wallets
    g = sub.add_parser("generate_wallets")
    g.add_argument("--chain",  required=True, choices=["solana", "evm"])
    g.add_argument("--count",  required=True, type=int)
    g.add_argument("--label",  required=True)
    g.add_argument("--tags",   default="")

    # send_native_multi
    s = sub.add_parser("send_native_multi")
    s.add_argument("--from-key",  required=True, dest="from_key")
    s.add_argument("--label",     required=True)
    s.add_argument("--amount",    required=True, type=float)
    s.add_argument("--chain",     required=True, choices=["solana", "evm"])
    s.add_argument("--rpc",       default=None)
    s.add_argument("--tag",       default=None)
    s.add_argument("--randomize", action="store_true")
    s.add_argument("--delay-min", type=int, default=1,  dest="delay_min")
    s.add_argument("--delay-max", type=int, default=30, dest="delay_max")
    s.add_argument("--retries",   type=int, default=3)

    # list_wallets
    lw = sub.add_parser("list_wallets")
    lw.add_argument("--chain",     default=None)
    lw.add_argument("--label",     default=None)
    lw.add_argument("--tag",       default=None)
    lw.add_argument("--show-keys", action="store_true", dest="show_keys")

    # close_token_accounts
    c = sub.add_parser("close_token_accounts")
    c.add_argument("--private-key",     required=True, dest="private_key")
    c.add_argument("--rpc",             default=None)
    c.add_argument("--close-non-empty", action="store_true", dest="close_non_empty")

    # scan_token_accounts
    sc = sub.add_parser("scan_token_accounts")
    sc.add_argument("--address", required=True)
    sc.add_argument("--rpc",     default=None)

    # get_balance_batch
    b = sub.add_parser("get_balance_batch")
    b.add_argument("--chain",  default=None)
    b.add_argument("--label",  default=None)
    b.add_argument("--tag",    default=None)
    b.add_argument("--rpc",    default=None)

    # tag_wallets
    t = sub.add_parser("tag_wallets")
    t.add_argument("--label", required=True)
    t.add_argument("--tag",   required=True)

    # group_summary
    sub.add_parser("group_summary")

    # delete_group
    d = sub.add_parser("delete_group")
    d.add_argument("--label", required=True)

    return p


DISPATCH = {
    "generate_wallets":     cmd_generate_wallets,
    "send_native_multi":    cmd_send_native_multi,
    "list_wallets":         cmd_list_wallets,
    "close_token_accounts": cmd_close_token_accounts,
    "scan_token_accounts":  cmd_scan_token_accounts,
    "get_balance_batch":    cmd_get_balance_batch,
    "tag_wallets":          cmd_tag_wallets,
    "group_summary":        cmd_group_summary,
    "delete_group":         cmd_delete_group,
}


def main():
    args = build_parser().parse_args()
    handler = DISPATCH.get(args.command)
    if not handler:
        _err(f"Unknown command: {args.command}")
    try:
        handler(args)
    except Exception as e:
        _err(str(e))


if __name__ == "__main__":
    main()
