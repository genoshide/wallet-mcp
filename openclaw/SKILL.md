# SKILL: wallet-mcp
description: Multi-chain wallet generator and manager. Supports Solana and EVM. All outputs are JSON.
version: 1.0.0
tool_path: ~/.openclaw/tools/wallet.py

---

## generate_wallets
Generate N new wallets and save them under a label.
```
command: python {tool_path} generate_wallets --chain <solana|evm> --count <N> --label <label> [--tags <tag1|tag2>]
```
Example:
```
python wallet.py generate_wallets --chain solana --count 50 --label airdrop1
```

---

## send_native_multi
Send SOL or ETH from one source wallet to all wallets in a group.
```
command: python {tool_path} send_native_multi --from-key <KEY> --label <label> --amount <AMOUNT> --chain <solana|evm> [--rpc <URL>] [--tag <tag>] [--randomize] [--delay-min 1] [--delay-max 30] [--retries 3]
```
Example:
```
python wallet.py send_native_multi --from-key 5Kd3... --label airdrop1 --amount 0.01 --chain solana --randomize --delay-min 2 --delay-max 15
```

---

## list_wallets
List wallets with optional filters. Private keys are masked by default.
```
command: python {tool_path} list_wallets [--chain <solana|evm>] [--label <label>] [--tag <tag>] [--show-keys]
```

---

## get_balance_batch
Fetch native balances for a wallet group.
```
command: python {tool_path} get_balance_batch [--chain <solana|evm>] [--label <label>] [--tag <tag>] [--rpc <URL>]
```

---

## close_token_accounts
Close empty SPL token accounts and reclaim rent SOL. (Solana only)
```
command: python {tool_path} close_token_accounts --private-key <KEY_B58> [--rpc <URL>] [--close-non-empty]
```

---

## scan_token_accounts
Scan all SPL token accounts for a Solana wallet (read-only, no changes).
```
command: python {tool_path} scan_token_accounts --address <PUBKEY> [--rpc <URL>]
```

---

## tag_wallets
Add a tag to all wallets in a label group.
```
command: python {tool_path} tag_wallets --label <label> --tag <tag>
```

---

## group_summary
Show all wallet groups with counts per chain.
```
command: python {tool_path} group_summary
```

---

## delete_group
Permanently delete all wallets in a group by label.
```
command: python {tool_path} delete_group --label <label>
```

---

## Error Format
```json
{"status": "error", "message": "..."}
```
