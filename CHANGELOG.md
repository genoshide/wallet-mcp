# Changelog

All notable changes to wallet-mcp are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-04-09

### Added
- **FastMCP server** (`src/wallet_mcp/server.py`) with 9 registered tools
- **`generate_wallets`** — generate N EVM or Solana wallets, save to CSV
- **`send_native_multi`** — send SOL/ETH from one wallet to a labeled group with retry, random delays, randomized amounts
- **`list_wallets`** — list wallets with chain/label/tag filters; private keys masked by default
- **`get_balance_batch`** — fetch native balances for a wallet group
- **`close_token_accounts`** — close empty SPL token accounts, reclaim rent SOL
- **`scan_token_accounts`** — read-only scan of SPL token accounts
- **`tag_wallets`** — add tags to a wallet group
- **`group_summary`** — show wallet groups with per-chain counts
- **`delete_group`** — permanently delete a wallet group
- **CSV storage** at `~/.wallet-mcp/wallets.csv` (configurable via `WALLET_DATA_DIR`)
- **python-dotenv** support — `.env` loaded automatically at server startup
- **Retry logic** in `core/utils.py` with `attempts >= 1` guard
- **Docker support** — multi-stage `Dockerfile` + `docker-compose.yml` with persistent volume
- **GitHub Actions** — `ci.yml` (test on push/PR, Python 3.11 + 3.12) and `release.yml` (build + GitHub Release on tag)
- **MCP Inspector** support via `mcp dev src/wallet_mcp/server.py`
- **Architecture diagram** — `assets/architecture.png` + `assets/architecture.md`
- `INSTALLATION.md`, `EXAMPLES.md`, `openclaw/SKILL.md`, `CONTRIBUTING.md`

### Fixed
- `rpc_url=None` no longer crashes core functions — all RPC functions fall back to `DEFAULT_RPC` when `None` is passed
- `get_token_accounts_by_owner` uses `TokenAccountOpts(program_id=...)` (correct solana-py API, not raw dict)
- Token account data parsing handles both `dict` and object forms across solana-py versions
- `retry(attempts=0)` raises `ValueError` instead of `TypeError: raise None`
- Variable shadowing (`w`) in `manager.py` batch balance loop

### Security
- Private keys masked in `list_wallets` output by default (`show_keys=False`)
- `.gitignore` excludes `wallets.csv`, `.env`, `__pycache__`, logs
- Docker runs as non-root `mcpuser`
