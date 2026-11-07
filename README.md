# mem20-ce

**mem20 Core Edition** — A trusted, auditable memory substrate for AI agents.

Grounded facts and simulated hypotheses never mix.  
Every retrieval can report index drift.  
Promotion requires evidence.  
Contamination rate on a clean store is **0.0**.

[![PyPI](https://img.shields.io/pypi/v/mem20-ce.svg)](https://pypi.org/project/mem20-ce/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Site](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://bythewayz66-glitch.github.io/mem20-ce/)

## Why this exists

Most agent memory systems treat every stored token as equally real.  
mem20-ce enforces a structural partition at the lowest write and index paths:

| Partition | Holds | Indexed for recall? |
|-----------|--------|---------------------|
| **Grounded** | Real observations, user statements, attested events | Yes |
| **Simulated** | Hypotheses, counterfactuals, model output | No |

Simulated content is refused from grounded indexes. Promotion from simulated → grounded requires evidence. Index/ledger disagreement is reported as a defect, not hidden.

This is the Core Edition extracted from the larger [mem20](https://github.com/bythewayz66-glitch/mem20) monorepo. The full organ estate remains in the original repository.

## Install

```bash
pip install mem20-ce
```

From source:

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
result = engine.recall("when does the deploy key rotate?")
print(result.hits)
print(result.healthy)

# Contamination must be 0.0 on a clean store
print(engine.contamination())
# ContaminationReport(contamination_rate=0.0, grounded_count=1, simulated_count=1, ...)

print(engine.health())
```

## CLI

```bash
mem20-ce remember "the deploy key rotates on the first Monday" --tag ops
mem20-ce simulate "perhaps the key was already rotated"
mem20-ce recall "deploy key"
mem20-ce contamination
mem20-ce health
```

## API surface

| Method | Purpose |
|--------|--------|
| `remember(content, *, tags=None)` | Store a **grounded** fact |
| `remember_simulated(content, *, tags=None)` | Store a **simulated** hypothesis |
| `promote(record_id, *, evidence)` | Promote simulated → grounded (requires evidence) |
| `recall(query, k=5)` | Retrieve from grounded partition only |
| `contamination()` | Audit report; rate must be `0.0` on a clean store |
| `health()` | Combined health + contamination + drift |

## Acceptance guarantees

These tests must pass before any release is called done:

1. Simulated records never appear in grounded indexes.
2. `remember()` rejects non-grounded origin by default.
3. Promotion without evidence is refused.
4. `contamination_rate == 0.0` on a clean store after mixed writes.
5. Index drift (ledger vs on-disk) is detectable and reportable.
6. Reads never write the ledger.

```bash
pytest tests/acceptance -q
```

## Package layout

```
mem20-ce/
├── src/mem20_ce/          # Core engine + API + CLI
├── tests/acceptance/      # Invariant acceptance tests
├── sdks/                  # Language SDKs (Python, Ruby, TypeScript, Perl)
├── docs/                  # GitHub Pages site
├── pyproject.toml
└── LICENSE                # Apache-2.0
```

## Links

- **PyPI:** https://pypi.org/project/mem20-ce/
- **Site:** https://bythewayz66-glitch.github.io/mem20-ce/
- **Full platform:** https://github.com/bythewayz66-glitch/mem20

## License

Apache License 2.0. See [LICENSE](LICENSE).
