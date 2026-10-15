# Measuring spread (proposal, NOT deployed)

1. **Passive (zero infra, recommended first):** every sealed record contains `"method": "BINGO STAR verify v1"` and an `hr1-` id. Weekly searches of GitHub code search, the agent board, X, and HF datasets for `"BINGO STAR verify v1"` / `"handoff/0.1"` / `hr1-`. Count distinct repos/authors. A record with a non-empty `previous` that carries an id we did not mint = a second-generation handoff.
2. **Opt-in public verify URL:** `https://<domain>/v/<hr1-id>` (e.g. a Vercel page). An agent may POST the receipt (sha + id only, no content) to get a "registered" timestamp; GET shows whether it was registered. Counts = registered ids, chains via `previous`. Must stay opt-in and off by default; no phone-home in the library.
3. **Distribution counts:** PyPI downloads (pypistats), GitHub stars/clones, MCP registry installs.
Success ladder: (a) outside use of the format, (b) with provenance kept, (c) a linked later handoff still carrying it.
Caveat: private use is invisible; downloads ≠ use.
