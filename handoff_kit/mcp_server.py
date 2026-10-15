"""Minimal dependency-free MCP server over stdio (JSON-RPC 2.0, newline-delimited)."""
import json, sys
from .core import create_handoff, validate_handoff, merge_handoff, seal, verify_receipt

ARR = {"type": "array", "items": {"type": "string"}}
TOOLS = [
    {"name": "create_handoff", "description": "Build a task handoff record (task, done, evidence, failed, unknowns, next_step) and seal it with a sha256 receipt so the next agent can confirm it was not altered.",
     "inputSchema": {"type": "object", "required": ["task"], "properties": {
         "task": {"type": "string"}, "done": ARR, "failed": ARR, "unknowns": ARR, "next_step": {"type": "string"},
         "evidence": {"type": "array", "items": {"type": "object", "properties": {"claim": {"type": "string"}, "how_verified": {"type": "string"}}}},
         "previous": ARR, "include_provenance": {"type": "boolean", "default": True}}}},
    {"name": "validate_handoff", "description": "Score a handoff's completeness, flag unverified claims, check any existing receipt, and issue a fresh receipt.",
     "inputSchema": {"type": "object", "required": ["handoff"], "properties": {"handoff": {"type": "object"}}}},
    {"name": "merge_handoff", "description": "Merge two handoffs into one sealed record linking both as previous.",
     "inputSchema": {"type": "object", "required": ["a", "b"], "properties": {"a": {"type": "object"}, "b": {"type": "object"}, "next_step": {"type": "string"}}}},
]

def call(name, a):
    if name == "create_handoff":
        return seal(create_handoff(a["task"], a.get("done"), a.get("evidence"), a.get("failed"), a.get("unknowns"),
                                   a.get("next_step", ""), a.get("previous"), a.get("include_provenance", True)))
    if name == "validate_handoff":
        return validate_handoff(a["handoff"])
    if name == "merge_handoff":
        return seal(merge_handoff(a["a"], a["b"], next_step=a.get("next_step")))
    raise KeyError(name)

def handle(msg):
    mid, m = msg.get("id"), msg.get("method")
    if mid is None: return None
    if m == "initialize":
        res = {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
               "capabilities": {"tools": {}}, "serverInfo": {"name": "handoff-kit", "version": "0.1.0"}}
    elif m == "tools/list": res = {"tools": TOOLS}
    elif m == "tools/call":
        p = msg.get("params", {})
        try:
            out = call(p.get("name"), p.get("arguments", {}))
            res = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}], "isError": False}
        except Exception as e:
            res = {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
    elif m == "ping": res = {}
    else: return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": mid, "result": res}

def main():
    for line in sys.stdin:
        if not line.strip(): continue
        out = handle(json.loads(line))
        if out: sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
