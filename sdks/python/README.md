# mem20-ce Python SDK

The Python package *is* the core. Install with:

```bash
pip install mem20-ce
```

```python
from mem20_ce import MemoryEngine
engine = MemoryEngine()
engine.remember("fact")
print(engine.contamination())
```
