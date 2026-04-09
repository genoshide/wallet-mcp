"""
Solana wallet operations: generation, SOL transfer, SPL token account management.
"""
import os
import base58

DEFAULT_RPC = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
LAMPORTS_PER_SOL = 1_000_000_000


# ── Keypair helpers ────────────────────────────────────────────────────────

def generate_solana_wallet() -> dict:
    """Generate a new Solana keypair. Private key is base58-encoded 64-byte secret."""
    from solders.keypair import Keypair
    kp = Keypair()
    return {
        "address":     str(kp.pubkey()),
        "private_key": base58.b58encode(bytes(kp)).decode(),
    }


def _keypair(private_key_b58: str):
    from solders.keypair import Keypair
    return Keypair.from_bytes(base58.b58decode(private_key_b58))


# ── Balance ────────────────────────────────────────────────────────────────

def get_sol_balance(address: str, rpc_url: str = DEFAULT_RPC) -> float:
    from solana.rpc.api import Client
    from solders.pubkey import Pubkey
    rpc_url = rpc_url or DEFAULT_RPC
    resp = Client(rpc_url).get_balance(Pubkey.from_string(address))
    return resp.value / LAMPORTS_PER_SOL


def get_sol_balances_batch(addresses: list[str], rpc_url: str = DEFAULT_RPC) -> list[dict]:
    from solana.rpc.api import Client
    from solders.pubkey import Pubkey
    rpc_url = rpc_url or DEFAULT_RPC
    client = Client(rpc_url)
    results = []
    for addr in addresses:
        try:
            bal = client.get_balance(Pubkey.from_string(addr)).value / LAMPORTS_PER_SOL
            results.append({"address": addr, "balance": bal, "status": "ok"})
        except Exception as e:
            results.append({"address": addr, "balance": None, "status": "error", "error": str(e)})
    return results


# ── Transfer ───────────────────────────────────────────────────────────────

def send_sol(
    from_private_key_b58: str,
    to_address: str,
    amount_sol: float,
    rpc_url: str = DEFAULT_RPC,
) -> str:
    """Transfer SOL. Returns transaction signature."""
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts
    from solders.pubkey import Pubkey
    from solders.system_program import transfer, TransferParams
    from solders.transaction import Transaction
    from solders.message import Message

    rpc_url = rpc_url or DEFAULT_RPC
    client  = Client(rpc_url)
    sender  = _keypair(from_private_key_b58)
    to_pub  = Pubkey.from_string(to_address)
    lamps   = int(amount_sol * LAMPORTS_PER_SOL)
    bh      = client.get_latest_blockhash().value.blockhash

    ix  = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=to_pub, lamports=lamps))
    msg = Message.new_with_blockhash([ix], sender.pubkey(), bh)
    tx  = Transaction([sender], msg, bh)

    result = client.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed"))
    return str(result.value)


# ── Token Account Closer ───────────────────────────────────────────────────

_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
_RENT_PER_ACCOUNT = 0.00203928  # approximate SOL rent for one token account


def get_token_accounts(owner_address: str, rpc_url: str = DEFAULT_RPC) -> list[dict]:
    """Return all SPL token accounts for `owner_address`."""
    from solana.rpc.api import Client
    from solana.rpc.types import TokenAccountOpts
    from solders.pubkey import Pubkey

    rpc_url = rpc_url or DEFAULT_RPC
    client = Client(rpc_url)
    owner  = Pubkey.from_string(owner_address)
    TOKEN  = Pubkey.from_string(_TOKEN_PROGRAM)

    resp = client.get_token_accounts_by_owner(
        owner,
        TokenAccountOpts(program_id=TOKEN),
        encoding="jsonParsed",
    )
    accounts = []
    if resp.value:
        for acc in resp.value:
            try:
                # solana-py returns account.data as dict when encoding=jsonParsed
                data = acc.account.data
                # Handle both dict and object forms across solana-py versions
                if isinstance(data, dict):
                    parsed = data.get("parsed", {})
                elif hasattr(data, "parsed"):
                    parsed = data.parsed
                else:
                    continue

                info   = parsed.get("info", {}) if isinstance(parsed, dict) else {}
                amount = info.get("tokenAmount", {})
                if not info or not amount:
                    continue

                accounts.append({
                    "pubkey":   str(acc.pubkey),
                    "mint":     info.get("mint", ""),
                    "amount":   int(amount.get("amount", 0)),
                    "decimals": int(amount.get("decimals", 0)),
                })
            except (KeyError, TypeError, AttributeError):
                continue
    return accounts


def close_token_accounts(
    private_key_b58: str,
    rpc_url: str = DEFAULT_RPC,
    close_non_empty: bool = False,
) -> dict:
    """
    Close empty SPL token accounts to reclaim rent SOL.
    Set close_non_empty=True to also close accounts with token balances.
    """
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction, AccountMeta
    from solders.transaction import Transaction
    from solders.message import Message

    rpc_url = rpc_url or DEFAULT_RPC
    TOKEN_PROG = Pubkey.from_string(_TOKEN_PROGRAM)
    CLOSE_IX   = bytes([9])   # CloseAccount opcode

    sender = _keypair(private_key_b58)
    owner  = str(sender.pubkey())

    all_accounts = get_token_accounts(owner, rpc_url)
    to_close     = [a for a in all_accounts if close_non_empty or a["amount"] == 0]

    if not to_close:
        return {"closed": 0, "skipped": len(all_accounts), "failed": 0,
                "total_found": len(all_accounts), "reclaimed_sol_estimate": 0.0}

    client  = Client(rpc_url)
    closed  = 0
    failed  = 0

    for acc in to_close:
        try:
            bh  = client.get_latest_blockhash().value.blockhash
            pub = Pubkey.from_string(acc["pubkey"])
            keys = [
                AccountMeta(pubkey=pub,           is_signer=False, is_writable=True),
                AccountMeta(pubkey=sender.pubkey(), is_signer=False, is_writable=True),
                AccountMeta(pubkey=sender.pubkey(), is_signer=True,  is_writable=False),
            ]
            ix  = Instruction(TOKEN_PROG, CLOSE_IX, keys)
            msg = Message.new_with_blockhash([ix], sender.pubkey(), bh)
            tx  = Transaction([sender], msg, bh)
            client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
            closed += 1
        except Exception:
            failed += 1

    return {
        "closed":                 closed,
        "failed":                 failed,
        "skipped":                len(all_accounts) - len(to_close),
        "total_found":            len(all_accounts),
        "reclaimed_sol_estimate": round(closed * _RENT_PER_ACCOUNT, 6),
    }
