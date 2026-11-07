# mem20-ce

**mem20 Core Edition** — A trusted, auditable memory substrate for AI agents.

Grounded facts and simulated hypotheses never mix.  
Every retrieval can report index drift.  
Promotion requires evidence.  
Contamination rate on a clean store is **0.0**.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

## Why this exists

Most agent memory systems treat every stored token as equally real.  
mem20-ce enforces a structural partition at the lowest write and index paths:

- **Grounded** memory holds facts from real observations, user statements, or events.
- **Simulated** memory holds hypotheses, counterfactuals, and model output.

Simulated content is refused from grounded indexes. Promotion from simulated → grounded requires evidence. Index/ledger disagreement is reported as a defect, not hidden.

This is the Core Edition extracted from the larger [mem20](https://github.com/bythewayz66-glitch/mem20) monorepo. The full organ estate remains in the original repository.

## Install

```bash
pip install mem20-ce
```

Or from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20-ce.git
cd mem20-ce
pip install -e ".[dev]"
```

## Quickstart

```python
from mem20_ce import MemoryEngine

engine = MemoryEngine(store_path="~/.mem20-ce/store")

# Grounded fact
engine.remember("the deploy key rotates on the first Monday", tags=["ops"])

# Simulated hypothesis (never reaches grounded indexes)
engine.remember_simulated("perhaps the key was rotated last week")

# Recall only returns grounded content
print(engine.recall("when does the deploy key rotate?"))

# Contamination must be 0.0 on a clean store
print(engine.contamination())  # {"contamination_rate": 0.0, ...}
```

## Acceptance guarantees

These tests must pass before any release is called done:

1. Simulated records never appear in grounded vector or BM25 indexes.
2. `remember()` rejects non-grounded origin by default.
3. Promotion without evidence is refused.
4. `contamination_rate == 0.0` on a clean store after mixed writes.
5. Index drift (ledger vs indexes) is detectable and reportable.
6. Reads never write the ledger.

Run them:

```bash
pytest tests/acceptance -q
```

## Package layout

```
mem20-ce/
├── src/mem20_ce/          # Core engine + API
├── tests/acceptance/     # Invariant acceptance tests
├── sdks/                 # Language SDKs (Python, Ruby, TypeScript, Perl)
├── docs/                 # GitHub Pages site source
├── pyproject.toml
└── LICENSE               # Apache-2.0
```

## License

Apache License 2.0. See [LICENSE](LICENSE).

Canonical full platform: [bythewayz66-glitch/mem20](https://github.com/bythewayz66-glitch/mem20).
