"""
Local test script — no network, no RPC needed.
Tests: wallet generation, storage, filtering, tagging, group summary, delete.

Run:
    python test_local.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# ── use a temp dir so tests don't touch real ~/.wallet-mcp ──────────────────
import tempfile
_TMP = tempfile.mkdtemp()
os.environ["WALLET_DATA_DIR"] = _TMP

# ── colour helpers ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0

def ok(name):
    global passed
    passed += 1
    print(f"  {GREEN}PASS{RESET}  {name}")

def fail(name, err):
    global failed
    failed += 1
    print(f"  {RED}FAIL{RESET}  {name}")
    print(f"     {RED}{err}{RESET}")

def section(title):
    print(f"\n{BOLD}{CYAN}-- {title} --{RESET}")

# ════════════════════════════════════════════════════════════════════════════
section("1. Imports")
# ════════════════════════════════════════════════════════════════════════════
try:
    from wallet_mcp.core.utils import random_amount, random_delay, retry, now_iso
    ok("core.utils")
except Exception as e:
    fail("core.utils", e)

try:
    from wallet_mcp.core.storage import (
        load_wallets, save_wallets_batch, filter_wallets,
        wallet_exists, tag_wallets, delete_wallets_by_label, _rewrite
    )
    ok("core.storage")
except Exception as e:
    fail("core.storage", e)

try:
    from wallet_mcp.core.generator import generate_wallets
    ok("core.generator")
except Exception as e:
    fail("core.generator", e)

try:
    from wallet_mcp.core.manager import (
        list_wallets, group_summary, tag_label, delete_group
    )
    ok("core.manager")
except Exception as e:
    fail("core.manager", e)

try:
    from wallet_mcp.core.evm import generate_evm_wallet
    ok("core.evm (generate)")
except Exception as e:
    fail("core.evm", e)

try:
    from wallet_mcp.core.solana import generate_solana_wallet
    ok("core.solana (generate)")
except Exception as e:
    fail("core.solana", e)

try:
    from wallet_mcp.server import mcp
    tools = list(mcp._tool_manager._tools.keys())
    assert len(tools) == 9, f"Expected 9 tools, got {len(tools)}"
    ok(f"FastMCP server  ({len(tools)} tools registered)")
except Exception as e:
    fail("FastMCP server", e)

# ════════════════════════════════════════════════════════════════════════════
section("2. EVM Wallet Generation")
# ════════════════════════════════════════════════════════════════════════════
try:
    w = generate_evm_wallet()
    assert w["address"].startswith("0x"), "address must start with 0x"
    assert len(w["address"]) == 42, "EVM address must be 42 chars"
    # eth_account key.hex() returns 64-char hex without 0x prefix
    assert len(w["private_key"]) == 64, f"private key must be 64 hex chars, got {len(w['private_key'])}"
    ok(f"EVM wallet  → {w['address'][:14]}…")
except Exception as e:
    fail("EVM wallet generation", e)

# ════════════════════════════════════════════════════════════════════════════
section("3. Solana Wallet Generation")
# ════════════════════════════════════════════════════════════════════════════
try:
    w = generate_solana_wallet()
    assert len(w["address"]) >= 32, "Solana address too short"
    assert len(w["private_key"]) >= 80, "private key too short"
    ok(f"Solana wallet  → {w['address'][:14]}…")
except Exception as e:
    fail("Solana wallet generation", e)

# ════════════════════════════════════════════════════════════════════════════
section("4. Batch Wallet Generation → CSV")
# ════════════════════════════════════════════════════════════════════════════
try:
    evm_wallets = generate_wallets("evm", 5, "test_evm", tags="smoke|evm")
    assert len(evm_wallets) == 5
    ok(f"Generated 5 EVM wallets  label=test_evm")
except Exception as e:
    fail("generate_wallets evm", e)

try:
    sol_wallets = generate_wallets("solana", 5, "test_sol", tags="smoke|sol")
    assert len(sol_wallets) == 5
    ok(f"Generated 5 Solana wallets  label=test_sol")
except Exception as e:
    fail("generate_wallets solana", e)

try:
    all_w = load_wallets()
    assert len(all_w) == 10, f"Expected 10 in CSV, got {len(all_w)}"
    ok(f"CSV now has {len(all_w)} wallets")
except Exception as e:
    fail("load_wallets", e)

# ════════════════════════════════════════════════════════════════════════════
section("5. Filtering")
# ════════════════════════════════════════════════════════════════════════════
try:
    evm = filter_wallets(chain="evm")
    assert len(evm) == 5
    ok(f"filter chain=evm  → {len(evm)} wallets")
except Exception as e:
    fail("filter by chain", e)

try:
    sol = filter_wallets(label="test_sol")
    assert len(sol) == 5
    ok(f"filter label=test_sol  → {len(sol)} wallets")
except Exception as e:
    fail("filter by label", e)

try:
    tagged = filter_wallets(tag="sol")
    assert len(tagged) == 5
    ok(f"filter tag=sol  → {len(tagged)} wallets")
except Exception as e:
    fail("filter by tag", e)

# ════════════════════════════════════════════════════════════════════════════
section("6. Duplicate Guard")
# ════════════════════════════════════════════════════════════════════════════
try:
    addr = load_wallets()[0]["address"]
    assert wallet_exists(addr) is True
    ok(f"wallet_exists(existing)  → True")
except Exception as e:
    fail("wallet_exists True", e)

try:
    assert wallet_exists("0xNOTEXIST") is False
    ok("wallet_exists(fake)  → False")
except Exception as e:
    fail("wallet_exists False", e)

# ════════════════════════════════════════════════════════════════════════════
section("7. Tagging")
# ════════════════════════════════════════════════════════════════════════════
try:
    updated = tag_wallets("test_evm", "funded")
    assert updated == 5
    ok(f"tag_wallets test_evm → funded  ({updated} updated)")
except Exception as e:
    fail("tag_wallets", e)

try:
    funded = filter_wallets(tag="funded")
    assert len(funded) == 5
    ok(f"filter tag=funded  → {len(funded)} wallets")
except Exception as e:
    fail("filter after tag", e)

try:
    # idempotent — tag again should not double-add
    updated2 = tag_wallets("test_evm", "funded")
    assert updated2 == 0, f"Expected 0 (already tagged), got {updated2}"
    ok("tag idempotent  (0 updated on re-tag)")
except Exception as e:
    fail("tag idempotent", e)

# ════════════════════════════════════════════════════════════════════════════
section("8. Group Summary")
# ════════════════════════════════════════════════════════════════════════════
try:
    groups = group_summary()
    labels = {g["label"]: g for g in groups}
    assert "test_evm" in labels
    assert "test_sol" in labels
    assert labels["test_evm"]["evm"] == 5
    assert labels["test_sol"]["solana"] == 5
    ok(f"group_summary  → {len(groups)} groups")
    for g in groups:
        print(f"     label={g['label']}  evm={g.get('evm',0)}  solana={g.get('solana',0)}  total={g['total']}")
except Exception as e:
    fail("group_summary", e)

# ════════════════════════════════════════════════════════════════════════════
section("9. list_wallets (key masking)")
# ════════════════════════════════════════════════════════════════════════════
try:
    wallets = list_wallets(label="test_evm")
    pk = wallets[0]["private_key"]
    assert "..." in pk or "…" in pk, f"key not masked: {pk}"
    ok(f"private key masked  → '{pk}'")
except Exception as e:
    fail("list_wallets key masking", e)

try:
    wallets_full = list_wallets(label="test_evm", show_keys=True)
    pk = wallets_full[0]["private_key"]
    # key is 64-char hex (no 0x prefix) — just confirm it's unmasked (long)
    assert len(pk) >= 60, f"key not fully shown: {pk}"
    assert "..." not in pk and "\u2026" not in pk, "key still masked"
    ok(f"show_keys=True shows full key  → {pk[:10]}…")
except Exception as e:
    fail("list_wallets show_keys", e)

# ════════════════════════════════════════════════════════════════════════════
section("10. Delete Group")
# ════════════════════════════════════════════════════════════════════════════
try:
    result = delete_group("test_evm")
    assert result["deleted"] == 5
    remaining = load_wallets()
    assert len(remaining) == 5, f"Expected 5 left, got {len(remaining)}"
    ok(f"delete_group test_evm  (deleted={result['deleted']}, remaining=5)")
except Exception as e:
    fail("delete_group", e)

# ════════════════════════════════════════════════════════════════════════════
section("11. Utils")
# ════════════════════════════════════════════════════════════════════════════
try:
    for _ in range(20):
        a = random_amount(1.0)
        assert 0.9 <= a <= 1.1, f"Out of range: {a}"
    ok("random_amount  (±10%, 20 samples)")
except Exception as e:
    fail("random_amount", e)

try:
    retry(lambda: None, attempts=1)
    ok("retry success  (1 attempt)")
except Exception as e:
    fail("retry success", e)

try:
    retry(lambda: None, attempts=3)
    ok("retry success  (3 attempts)")
except Exception as e:
    fail("retry success 3", e)

try:
    retry(lambda: 1/0, attempts=0)
    fail("retry(0) should raise ValueError", "no error raised")
except ValueError:
    ok("retry(attempts=0)  → ValueError guard")
except Exception as e:
    fail("retry(0) guard", e)

try:
    call_count = {"n": 0}
    def _flaky():
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError("flaky")
        return "ok"
    result = retry(_flaky, attempts=3, delay=0)
    assert result == "ok"
    assert call_count["n"] == 3
    ok(f"retry with flaky fn  (succeeded on attempt 3)")
except Exception as e:
    fail("retry flaky fn", e)

try:
    ts = now_iso()
    assert ts.endswith("Z")
    assert "T" in ts
    ok(f"now_iso  → {ts}")
except Exception as e:
    fail("now_iso", e)

# ════════════════════════════════════════════════════════════════════════════
section("12. MCP Tool Dispatch (server layer)")
# ════════════════════════════════════════════════════════════════════════════
try:
    from wallet_mcp.server import generate_wallets as srv_gen
    r = srv_gen(chain="evm", count=3, label="srv_test")
    assert r["status"] == "success"
    assert r["generated"] == 3
    assert len(r["wallets"]) == 3
    ok(f"server.generate_wallets  → generated={r['generated']}")
except Exception as e:
    fail("server.generate_wallets", e)

try:
    from wallet_mcp.server import list_wallets as srv_list
    r = srv_list(label="srv_test")
    assert r["status"] == "success"
    assert r["count"] == 3
    ok(f"server.list_wallets  → count={r['count']}")
except Exception as e:
    fail("server.list_wallets", e)

try:
    from wallet_mcp.server import group_summary as srv_grp
    r = srv_grp()
    assert r["status"] == "success"
    ok(f"server.group_summary  → {len(r['groups'])} groups")
except Exception as e:
    fail("server.group_summary", e)

try:
    from wallet_mcp.server import tag_wallets as srv_tag
    r = srv_tag(label="srv_test", tag="autotest")
    assert r["status"] == "success"
    ok(f"server.tag_wallets  → updated={r['updated']}")
except Exception as e:
    fail("server.tag_wallets", e)

try:
    from wallet_mcp.server import delete_group as srv_del
    r = srv_del(label="srv_test")
    assert r["status"] == "success"
    ok(f"server.delete_group  → deleted={r['deleted']}")
except Exception as e:
    fail("server.delete_group", e)

try:
    from wallet_mcp.server import generate_wallets as srv_gen2
    r = srv_gen2(chain="INVALID", count=5, label="x")
    assert r["status"] == "error"
    ok(f"server error handling  → {r['message'][:40]}")
except Exception as e:
    fail("server error handling", e)

# ════════════════════════════════════════════════════════════════════════════
# Result
# ════════════════════════════════════════════════════════════════════════════
import shutil
shutil.rmtree(_TMP, ignore_errors=True)

total = passed + failed
print(f"\n{'='*50}")
if failed == 0:
    print(f"{GREEN}{BOLD}  ALL {passed}/{total} TESTS PASSED{RESET}")
else:
    print(f"{RED}{BOLD}  {failed} FAILED  /  {passed} PASSED{RESET}")
print(f"{'='*50}\n")
sys.exit(0 if failed == 0 else 1)
