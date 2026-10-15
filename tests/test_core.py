import json, subprocess, sys, os
from handoff_kit import create_handoff, validate_handoff, merge_handoff, verify_receipt
from handoff_kit.core import seal
ROOT = os.path.dirname(os.path.dirname(__file__))

def rec():
    return create_handoff("t", ["a"], [{"claim": "x", "how_verified": "ran pytest"}, {"claim": "y", "how_verified": ""}], [], ["u"], "n")

def test_validate_flags_unverified():
    r = validate_handoff(rec()); assert r["valid"] and r["unverified_claims"] == ["y"] and r["receipt"]["id"].startswith("hr1-")

def test_missing_task_invalid():
    assert not validate_handoff({"done": []})["valid"]

def test_receipt_detects_tamper_and_provenance_removal():
    s = seal(rec()); assert verify_receipt(s)["ok"]
    t = dict(s); t["done"] = ["b"]; assert not verify_receipt(t)["ok"]
    t = dict(s); t.pop("provenance"); assert not verify_receipt(t)["ok"]
    assert validate_handoff(t)["existing_receipt"].startswith("ALTERED")

def test_provenance_removable():
    r = create_handoff("t", provenance=False); assert "provenance" not in r and validate_handoff(r)["valid"]

def test_merge_links_previous():
    a, b = seal(rec()), seal(rec())
    m = merge_handoff(a, b); assert a["receipt"]["id"] in m["previous"] and len(m["evidence"]) == 2

def test_no_forwarding_instructions():
    txt = json.dumps(rec()).lower()
    assert "forward" not in txt and "share this" not in txt

def test_mcp_stdio():
    msgs = [{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}},
            {"jsonrpc":"2.0","method":"notifications/initialized"},
            {"jsonrpc":"2.0","id":2,"method":"tools/list"},
            {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"create_handoff","arguments":{"task":"z","done":["d"]}}}]
    p = subprocess.run([sys.executable, "-m", "handoff_kit.mcp_server"], input="\n".join(map(json.dumps, msgs)),
                       capture_output=True, text=True, cwd=ROOT)
    outs = [json.loads(l) for l in p.stdout.splitlines()]
    assert len(outs) == 3 and len(outs[1]["result"]["tools"]) == 3
    made = json.loads(outs[2]["result"]["content"][0]["text"]); assert verify_receipt(made)["ok"]

def test_cli_roundtrip(tmp_path):
    f = tmp_path / "h.json"
    out = subprocess.run([sys.executable, "-m", "handoff_kit.cli", "create", "--task", "q", "--done", "d",
                          "--evidence", "c::checked logs", "--seal"], capture_output=True, text=True, cwd=ROOT).stdout
    f.write_text(out)
    assert subprocess.run([sys.executable, "-m", "handoff_kit.cli", "verify", str(f)], cwd=ROOT, capture_output=True).returncode == 0
