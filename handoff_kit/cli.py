import argparse, json, sys
from .core import create_handoff, validate_handoff, merge_handoff, verify_receipt, seal

def _load(p):
    return json.load(sys.stdin if p == "-" else open(p))

def main(argv=None):
    ap = argparse.ArgumentParser(prog="handoff", description="Agent task handoff records")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("--task", required=True)
    c.add_argument("--done", action="append", default=[]); c.add_argument("--failed", action="append", default=[])
    c.add_argument("--unknown", action="append", default=[]); c.add_argument("--next", default="")
    c.add_argument("--evidence", action="append", default=[], help="'claim::how verified'")
    c.add_argument("--previous", action="append"); c.add_argument("--no-provenance", action="store_true")
    c.add_argument("--seal", action="store_true")
    v = sub.add_parser("validate"); v.add_argument("file")
    s = sub.add_parser("seal"); s.add_argument("file")
    r = sub.add_parser("verify"); r.add_argument("file")
    m = sub.add_parser("merge"); m.add_argument("a"); m.add_argument("b"); m.add_argument("--next")
    a = ap.parse_args(argv)
    if a.cmd == "create":
        ev = [dict(zip(("claim", "how_verified"), (x.split("::", 1) + [""])[:2])) for x in a.evidence]
        out = create_handoff(a.task, a.done, ev, a.failed, a.unknown, a.next, a.previous, not a.no_provenance)
        if a.seal: out = seal(out)
    elif a.cmd == "validate": out = validate_handoff(_load(a.file))
    elif a.cmd == "seal": out = seal(_load(a.file))
    elif a.cmd == "verify":
        out = verify_receipt(_load(a.file)); print(json.dumps(out, indent=2)); return 0 if out["ok"] else 1
    else: out = merge_handoff(_load(a.a), _load(a.b), next_step=a.next)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("valid", True) else 1

if __name__ == "__main__":
    sys.exit(main())
