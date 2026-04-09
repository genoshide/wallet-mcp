# Examples

## Airdrop Campaign (Solana)

### 1. Generate wallets for the campaign
```
generate_wallets(chain="solana", count=100, label="drop_apr", tags="airdrop|season1")
```

### 2. Check they were created
```
group_summary()
```
Output:
```json
{
  "groups": [{"label": "drop_apr", "solana": 100, "evm": 0, "total": 100}]
}
```

### 3. Fund all wallets from your main wallet
```
send_native_multi(
  from_key="5Kd3NBo...",
  label="drop_apr",
  amount=0.05,
  chain="solana",
  randomize=True,
  delay_min=2,
  delay_max=12,
  retries=3
)
```

### 4. Verify balances
```
get_balance_batch(label="drop_apr", chain="solana")
```

### 5. Tag funded wallets
```
tag_wallets(label="drop_apr", tag="funded")
```

---

## Multi-Chain Wallet Management

### Generate EVM wallets
```
generate_wallets(chain="evm", count=20, label="eth_test", tags="ethereum|testgroup")
```

### List only Solana wallets
```
list_wallets(chain="solana")
```

### List wallets by tag
```
list_wallets(tag="funded")
```

### Get all balances across chains
```
get_balance_batch()
```

---

## Solana Rent Recovery

### Scan token accounts first (read-only)
```
scan_token_accounts(address="So1anaWa11etPubkey...")
```
Output:
```json
{
  "total": 23,
  "empty": 18,
  "non_empty": 5,
  "accounts": [...]
}
```

### Close empty accounts
```
close_token_accounts(private_key="5Kd3NBo...")
```
Output:
```json
{
  "closed": 18,
  "failed": 0,
  "skipped": 5,
  "total_found": 23,
  "reclaimed_sol_estimate": 0.036707
}
```

---

## Custom RPC Endpoints

Pass `rpc` parameter to any tool that interacts with the chain:

```
# Helius (Solana)
get_balance_batch(label="drop_apr", rpc="https://mainnet.helius-rpc.com/?api-key=xxx")

# QuickNode (Solana)
send_native_multi(..., rpc="https://your-endpoint.quiknode.pro/token/")

# Alchemy (EVM)
get_balance_batch(chain="evm", label="eth_test", rpc="https://eth-mainnet.g.alchemy.com/v2/key")

# BSC
send_native_multi(..., chain="evm", rpc="https://bsc-dataseed.binance.org/")

# Polygon
send_native_multi(..., chain="evm", rpc="https://polygon-rpc.com")
```

---

## Wallet Cleanup

### Delete a group permanently
```
delete_group(label="old_campaign")
```

### Check what will be deleted first
```
list_wallets(label="old_campaign")
```

---

## Natural Language (Claude Desktop)

These prompts work directly in Claude Desktop after installing wallet-mcp:

- _"Generate 50 Solana wallets for my new airdrop, label it launch_may"_
- _"Send 0.02 SOL to all launch_may wallets with random delays between 3 and 20 seconds"_
- _"How much total SOL do my launch_may wallets hold?"_
- _"Tag all launch_may wallets as funded"_
- _"Show me all my wallet groups"_
- _"Scan token accounts on wallet So1ana... and close the empty ones to reclaim SOL"_
- _"Create 30 EVM wallets for my Ethereum test group"_
- _"List all Solana wallets with the tag funded"_
