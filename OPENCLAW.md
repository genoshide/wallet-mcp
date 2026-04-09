# OpenClaw Integration Guide

Connect wallet-mcp to **Telegram, WhatsApp, Discord** and 20+ messaging platforms using [OpenClaw](https://openclaw.ai) — a self-hosted AI gateway.

---

## How It Works

```
Telegram → OpenClaw agent (AI model) → openclaw/wallet.py → wallet_mcp core → CSV / Blockchain
```

OpenClaw routes messages to an AI agent. The agent uses `wallet.py` — a thin Python wrapper — to call wallet-mcp functions and return formatted results directly. **No MCP protocol needed; it's a direct Python import.**

---

## Quick Setup (VPS / Ubuntu 24.04)

### 1. Install UV and wallet-mcp

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
uv tool install git+https://github.com/genoshide/wallet-mcp.git
```

### 2. Configure OpenClaw channels

```bash
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  channels: {
    telegram: {
      botToken: "YOUR_BOT_TOKEN_HERE",
    },
  },
}
EOF
```

### 3. Configure gateway + agent

```bash
openclaw config set gateway.mode local
openclaw config set acp.defaultAgent main
```

### 4. Set your AI model

```bash
# Choose ONE of:
openclaw config set agents.defaults.model "anthropic/claude-sonnet-4-5"
openclaw config set agents.defaults.model "openrouter/google/gemini-3-flash-preview"
openclaw config set agents.defaults.model "openai/gpt-4o-mini"
```

### 5. Install the skill + tool wrapper

```bash
mkdir -p ~/.agents/skills/wallet-mcp ~/.openclaw/tools

curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/SKILL.md \
  -o ~/.agents/skills/wallet-mcp/SKILL.md

curl -fsSL https://raw.githubusercontent.com/genoshide/wallet-mcp/main/openclaw/wallet.py \
  -o ~/.openclaw/tools/wallet.py && chmod +x ~/.openclaw/tools/wallet.py
```

### 6. Start the gateway

```bash
openclaw gateway install
systemctl --user start openclaw-gateway.service
```

---

## Choose Your AI Model

| Provider | Model ID | Get Key |
|---|---|---|
| Anthropic (Claude) | `anthropic/claude-sonnet-4-5` | [console.anthropic.com](https://console.anthropic.com) |
| OpenRouter (all models) | `openrouter/google/gemini-3-flash-preview` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Google (Gemini) | `google/gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI (GPT) | `openai/gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |

---

## Test Your Bot

Once running, send your Telegram bot:

```
show my wallet groups
generate 10 solana wallets for airdrop1
how much SOL do my airdrop1 wallets have?
```

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: wallet.py` | Script not executable | `chmod +x ~/.openclaw/tools/wallet.py` |
| `ModuleNotFoundError: wallet_mcp` | wallet-mcp not installed | `uv tool install git+https://...` |
| `No wallets found` | Wrong label | Send "show my wallet groups" to check labels |
| `which agent?` loop | defaultAgent not set | `openclaw config set acp.defaultAgent main` |

---

## Environment Variables

Set in `~/.openclaw/.env` or export before starting the gateway:

```bash
export SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=xxx
export EVM_RPC_URL=https://mainnet.infura.io/v3/your_key
export WALLET_DATA_DIR=~/.wallet-mcp
```
