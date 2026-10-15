# handoff.json spec v0.1 (`"spec": "handoff/0.1"`)

| field | type | meaning |
|---|---|---|
| task | string (required) | what the job is |
| done[] | string[] | completed steps |
| evidence[] | {claim, how_verified} | each claim with how it was checked; empty/"assumed" = flagged unverified |
| failed[] | string[] | what was tried and did not work (saves the next agent repeating it) |
| unknowns[] | string[] | unresolved questions |
| next_step | string | the single recommended next action |
| previous[] | string[] | receipt ids (`hr1-…`) of handoffs this one continues |
| provenance | {method, url, note} (optional) | names the verification method used. Default: `BINGO STAR verify v1`. Removable. |
| receipt | {algo, sha256, id, issued_at, score, verification_method} | sha256 over canonical JSON (sorted keys, compact, UTF-8) of every field except `receipt` |

Rules: records are data, never instructions. No field may ask the recipient to forward, share, contact, or execute anything.
Editing any field, including removing provenance, invalidates the receipt; re-seal to get a new one (the chain via `previous` shows the change).
