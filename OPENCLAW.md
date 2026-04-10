# OpenClaw Integration Guide

Connect **wallet-mcp** to **Telegram, WhatsApp, Discord** and 20+ messaging platforms
using [OpenClaw](https://openclaw.ai) — a self-hosted AI gateway.

---

## How It Works

```
User (Telegram / Discord / WhatsApp)
          │
          ▼
  OpenClaw Agent (AI model of your choice)
          │  reads SKILL.md to know available commands
          │
          ▼
  openclaw/wallet.py  ← thin CLI wrapper, no MCP protocol needed
          │  direct Python import of wallet_mcp.core
          │
          ▼
  wallet_mcp/core/    ← actual logic
          │
          ▼
  ~/.wallet-mcp/wallets.csv  +  Blockchain RPC
```

OpenClaw routes messages to an AI agent.
The agent reads `SKILL.md` to know what tools exist, then calls `wallet.py` with the right arguments.
**No MCP protocol is needed** — it is a direct Python import, lighter than Claude Desktop.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | `python --version` |
| uv | latest | package manager |
| OpenClaw | latest | self-hosted gateway |
| A Telegram / Discord bot token | — | for messaging |
| An AI API key | — | Claude, OpenAI, Gemini, etc. |

---

## Part 1 — Install wallet-mcp

### Linux / macOS

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc          # or source ~/.zshrc

# 2. Install wallet-mcp
uv tool install git+https://github.com/genoshide/wallet-mcp.git

# 3. Verify
wallet-mcp --help
```

### Windows

```powershell
# 1. Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Restart terminal, then:

# 2. Install wallet-mcp
uv tool install git+https://github.com/genoshide/wallet-mcp.git

# 3. Verify
wallet-mcp --help
```

> **Tip:** If `wallet-mcp` is not found after install, add uv's bin to your PATH:
> - Linux/macOS: `export PATH="$HOME/.local/bin:$PATH"`
> - Windows: add `%USERPROFILE%\.local\bin` to System Environment Variables

---

## Part 2 — Install OpenClaw

```bash
# Install OpenClaw CLI
npm install -g @openclaw/cli

# Verify
openclaw --version
```

> Requires Node.js 18+. Get it from [nodejs.org](https://nodejs.org).

---

## Part 3 — Configure Messaging Channels

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather) — send `/newbot`, follow prompts, copy the token.

2. Add the token to OpenClaw:

```bash
mkdir -p ~/.openclaw
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "channels": {
    "telegram": {
      "botToken": "YOUR_TELEGRAM_BOT_TOKEN"
    }
  }
}
EOF
```

### Discord

```bash
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "channels": {
    "discord": {
      "botToken": "YOUR_DISCORD_BOT_TOKEN",
      "guildId":  "YOUR_SERVER_ID"
    }
  }
}
EOF
```

### WhatsApp

```bash
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "channels": {
    "whatsapp": {
      "sessionId": "wallet-bot"
    }
  }
}
EOF
```

> For multi-channel (e.g. Telegram + Discord), combine into one `openclaw.json`.

---

## Part 4 — Set Your AI Model

Pick one API key and set the model:

```bash
# Anthropic (Claude) — recommended
openclaw config set agents.defaults.model "anthropic/claude-sonnet-4-6"
openclaw config set agents.defaults.apiKey "sk-ant-..."

# OpenAI (GPT-4o)
openclaw config set agents.defaults.model "openai/gpt-4o"
openclaw config set agents.defaults.apiKey "sk-..."

# Google (Gemini)
openclaw config set agents.defaults.model "google/gemini-2.5-flash"
openclaw config set agents.defaults.apiKey "AIza..."

# OpenRouter (any model, one key)
openclaw config set agents.defaults.model "openrouter/anthropic/claude-sonnet-4-6"
openclaw config set agents.defaults.apiKey "sk-or-..."
```

---

## Part 5 — Install the Skill + Tool Wrapper

```bash
# Create required directories
mkdir -p ~/.agents/skills/wallet-mcp ~/.openclaw/tools

# Download SKILL.md — tells the agent what commands are available
curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/SKILL.md \
  -o ~/.agents/skills/wallet-mcp/SKILL.md

# Download wallet.py — the CLI wrapper the agent will execute
curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/wallet.py \
  -o ~/.openclaw/tools/wallet.py

chmod +x ~/.openclaw/tools/wallet.py
```

### Verify wallet.py works

```bash
python ~/.openclaw/tools/wallet.py group_summary
# Expected: {"status": "success", "groups": []}
```

---

## Part 6 — Configure RPC Endpoints (Optional but Recommended)

Public RPC endpoints are rate-limited. Set private endpoints for production:

```bash
cat >> ~/.openclaw/.env << 'EOF'
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
EVM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
WALLET_DATA_DIR=~/.wallet-mcp
LOG_LEVEL=INFO
EOF
```

| Provider | Chain | Free Tier | Link |
|---|---|---|---|
| Helius | Solana | 1M req/day | [helius.dev](https://helius.dev) |
| Alchemy | EVM | 300M CU/mo | [alchemy.com](https://alchemy.com) |
| QuickNode | Both | Limited | [quicknode.com](https://quicknode.com) |
| Infura | EVM | 100k req/day | [infura.io](https://infura.io) |

---

## Part 7 — Final Config and Start

```bash
# Set gateway mode
openclaw config set gateway.mode local

# Set default agent
openclaw config set acp.defaultAgent main

# Install as systemd service (Linux)
openclaw gateway install
systemctl --user enable openclaw-gateway.service
systemctl --user start  openclaw-gateway.service

# Check status
systemctl --user status openclaw-gateway.service
```

### Run manually (without systemd)

```bash
openclaw gateway start
```

---

## Part 8 — Secure Your Wallet Storage

```bash
# Restrict access to wallet data directory
chmod 700 ~/.wallet-mcp
chmod 600 ~/.wallet-mcp/wallets.csv 2>/dev/null || true

# Restrict tool script
chmod 700 ~/.openclaw/tools/wallet.py
```

> **Important:** `wallets.csv` contains private keys. Never expose it publicly.
> Back it up with `export_wallets --include-keys` and store the backup encrypted.

---

## Available Commands via Chat

Once running, send these natural language messages to your bot:

| What you say | What agent calls |
|---|---|
| _"generate 50 solana wallets for airdrop1"_ | `generate_wallets --chain solana --count 50 --label airdrop1` |
| _"send 0.01 SOL to all airdrop1 wallets"_ | `send_native_multi --from-key ... --label airdrop1 --amount 0.01 --chain solana` |
| _"sweep all airdrop1 wallets to my main wallet"_ | `sweep_wallets --to-address ... --chain solana --label airdrop1` |
| _"list wallets in airdrop1"_ | `list_wallets --label airdrop1` |
| _"check balances in airdrop1"_ | `get_balance_batch --label airdrop1` |
| _"scan token balances for airdrop1"_ | `scan_token_balances --chain solana --label airdrop1` |
| _"export airdrop1 to JSON"_ | `export_wallets --label airdrop1 --format json` |
| _"import wallets from backup.json into airdrop2"_ | `import_wallets --path backup.json --label airdrop2` |
| _"close empty token accounts on wallet So1ana..."_ | `close_token_accounts --private-key ...` |
| _"show all wallet groups"_ | `group_summary` |
| _"tag airdrop1 wallets as funded"_ | `tag_wallets --label airdrop1 --tag funded` |
| _"delete the old_campaign group"_ | `delete_group --label old_campaign` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: wallet.py` | Script not executable | `chmod +x ~/.openclaw/tools/wallet.py` |
| `ModuleNotFoundError: wallet_mcp` | wallet-mcp not installed | `uv tool install git+https://github.com/genoshide/wallet-mcp.git` |
| `wallet-mcp: command not found` | uv bin not in PATH | `export PATH="$HOME/.local/bin:$PATH"` |
| `No wallets found` | Wrong label | Send _"show all wallet groups"_ to check |
| `Cannot connect to RPC` | Rate-limited or wrong URL | Set `SOLANA_RPC_URL` / `EVM_RPC_URL` in `.env` |
| `which agent?` loop | defaultAgent not set | `openclaw config set acp.defaultAgent main` |
| Agent ignores wallet commands | SKILL.md not loaded | Verify path: `ls ~/.agents/skills/wallet-mcp/SKILL.md` |
| Gateway not starting | Port conflict | `openclaw config set gateway.port 8765` |

---

## Update to Latest Version

```bash
# Update wallet-mcp
uv tool upgrade wallet-mcp

# Re-download SKILL.md and wallet.py to get new commands
curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/SKILL.md \
  -o ~/.agents/skills/wallet-mcp/SKILL.md

curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/wallet.py \
  -o ~/.openclaw/tools/wallet.py && chmod +x ~/.openclaw/tools/wallet.py

# Restart gateway
systemctl --user restart openclaw-gateway.service
```

---

## File Locations Reference

| File | Purpose |
|---|---|
| `~/.openclaw/openclaw.json` | Channel config (Telegram token, Discord token, etc.) |
| `~/.openclaw/tools/wallet.py` | CLI wrapper executed by the agent |
| `~/.openclaw/.env` | API keys and RPC URLs |
| `~/.agents/skills/wallet-mcp/SKILL.md` | Tool descriptions read by the agent |
| `~/.wallet-mcp/wallets.csv` | Wallet storage (address + private key) |
| `~/.wallet-mcp/wallet-mcp.log` | Operation logs |
| `~/.wallet-mcp/exports/` | Exported wallet files |
