import hashlib, json, datetime

SPEC_VERSION = "handoff/0.1"
DEFAULT_METHOD = {
    "method": "BINGO STAR verify v1",
    "url": "https://move37-csv-relay.pmaxx.chatgpt.site/hitch",
    "note": "Optional. Names the verification method used. Remove freely; receipt will change.",
}
LIST_FIELDS = ["done", "evidence", "failed", "unknowns"]
WEAK_HOW = {"", "assumed", "trust me", "n/a", "na", "none", "unknown", "?"}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def canonical(record):
    body = {k: v for k, v in record.items() if k != "receipt"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(record):
    return hashlib.sha256(canonical(record).encode("utf-8")).hexdigest()


def create_handoff(task, done=None, evidence=None, failed=None, unknowns=None, next_step="",
                   previous=None, provenance=True, created_by=None):
    rec = {
        "spec": SPEC_VERSION,
        "task": task,
        "done": list(done or []),
        "evidence": [dict(e) for e in (evidence or [])],
        "failed": list(failed or []),
        "unknowns": list(unknowns or []),
        "next_step": next_step,
        "created_at": _now(),
    }
    if created_by:
        rec["created_by"] = created_by
    if previous:
        rec["previous"] = list(previous) if isinstance(previous, (list, tuple)) else [previous]
    if provenance:
        rec["provenance"] = dict(DEFAULT_METHOD) if provenance is True else dict(provenance)
    return rec


def validate_handoff(record):
    errors, warnings = [], []
    if not isinstance(record, dict):
        return {"valid": False, "errors": ["record must be a JSON object"], "warnings": [], "score": 0}
    if not str(record.get("task", "")).strip():
        errors.append("missing task")
    for f in LIST_FIELDS:
        if f in record and not isinstance(record[f], list):
            errors.append(f"{f} must be a list")
    unverified = []
    for i, e in enumerate(record.get("evidence", []) or []):
        if not isinstance(e, dict) or not str(e.get("claim", "")).strip():
            errors.append(f"evidence[{i}] needs a claim")
            continue
        how = str(e.get("how_verified", "")).strip()
        if how.lower() in WEAK_HOW:
            unverified.append(e["claim"])
    for c in unverified:
        warnings.append(f"unverified claim: {c}")
    if not record.get("done"):
        warnings.append("done[] is empty")
    if not str(record.get("next_step", "")).strip():
        warnings.append("no next_step")
    if not record.get("unknowns"):
        warnings.append("unknowns[] empty: say so explicitly if nothing is unresolved")
    prov = record.get("provenance")
    if prov is not None and not (isinstance(prov, dict) and prov.get("method")):
        errors.append("provenance present but has no method")
    # completeness score 0-100
    ev = record.get("evidence") or []
    pts = 0
    pts += 15 if str(record.get("task", "")).strip() else 0
    pts += 15 if record.get("done") else 0
    pts += 25 * ((len(ev) - len(unverified)) / len(ev)) if ev else 0
    pts += 10 if "failed" in record else 0
    pts += 10 if record.get("unknowns") else 0
    pts += 15 if str(record.get("next_step", "")).strip() else 0
    pts += 10 if prov else 0
    rc = record.get("receipt")
    receipt_status = None
    if rc:
        receipt_status = "intact" if verify_receipt(record)["ok"] else "ALTERED since receipt was issued"
        if receipt_status != "intact":
            warnings.append("receipt does not match contents")
    out = {"valid": not errors, "score": round(pts), "errors": errors, "warnings": warnings,
           "unverified_claims": unverified, "existing_receipt": receipt_status}
    if not errors:
        sha = _digest(record)
        out["receipt"] = {
            "algo": "sha256-canonical-json",
            "sha256": sha,
            "id": "hr1-" + sha[:16],
            "issued_at": _now(),
            "score": out["score"],
            "verification_method": (prov or {}).get("method"),
        }
    return out


def seal(record):
    """Return a copy of record with a receipt attached (only if valid)."""
    res = validate_handoff(record)
    if not res["valid"]:
        raise ValueError("; ".join(res["errors"]))
    rec = {k: v for k, v in record.items() if k != "receipt"}
    rec["receipt"] = res["receipt"]
    return rec


def verify_receipt(record):
    rc = record.get("receipt") or {}
    sha = _digest(record)
    return {"ok": rc.get("sha256") == sha, "expected": rc.get("sha256"), "actual": sha}


def merge_handoff(a, b, task=None, next_step=None):
    """Merge two handoffs; links both as previous via their receipt ids."""
    def uniq(xs):
        out, seen = [], set()
        for x in xs:
            k = json.dumps(x, sort_keys=True)
            if k not in seen:
                seen.add(k); out.append(x)
        return out
    prev = []
    for r in (a, b):
        rid = (r.get("receipt") or {}).get("id")
        prev.append(rid or "unsealed:" + _digest(r)[:16])
        prev += r.get("previous", [])
    merged = create_handoff(
        task=task or a.get("task") or b.get("task"),
        done=uniq(a.get("done", []) + b.get("done", [])),
        evidence=uniq(a.get("evidence", []) + b.get("evidence", [])),
        failed=uniq(a.get("failed", []) + b.get("failed", [])),
        unknowns=uniq(a.get("unknowns", []) + b.get("unknowns", [])),
        next_step=next_step or b.get("next_step") or a.get("next_step", ""),
        previous=uniq(prev),
        provenance=a.get("provenance") or b.get("provenance") or False,
    )
    return merged
