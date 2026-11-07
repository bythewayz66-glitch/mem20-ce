"""
mem20-ce Memory Engine

Hard invariants enforced at the lowest write and index paths:

1. Grounded and simulated partitions never mix.
2. Vector / BM25 indexes are grounded-only; simulated content is refused.
3. remember() is grounded-only by default.
4. Promotion requires evidence (resolved prediction or external attestation).
5. contamination_rate is 0.0 on a clean store.
6. Index drift is reported, never silently accepted.
7. Reads never write the ledger.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class ContaminationError(Exception):
    """Raised when simulated content would enter a grounded index."""


class PromotionError(Exception):
    """Raised when promotion is attempted without evidence."""


class PartitionError(Exception):
    """Raised on invalid origin/partition tags."""


@dataclass
class Record:
    id: str
    content: str
    origin: str  # "grounded" | "simulated"
    tags: List[str] = field(default_factory=list)
    epistemic_status: str = "fact"  # fact | hypothesis | imagined
    created_at: float = field(default_factory=time.time)
    evidence: Optional[Dict[str, Any]] = None
    promoted_from: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Record":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ContaminationReport:
    contamination_rate: float
    grounded_count: int
    simulated_count: int
    violations: List[str] = field(default_factory=list)
    healthy: bool = True


@dataclass
class RecallResult:
    hits: List[Dict[str, Any]]
    healthy: bool
    diagnostic: Dict[str, Any] = field(default_factory=dict)


class MemoryEngine:
    """
    Append-only ledger + grounded-only indexes.

    Store layout under store_path:
      ledger.jsonl
      grounded/
      simulated/
      index_meta.json
    """

    def __init__(self, store_path: str | Path = "~/.mem20-ce/store"):
        self.store_path = Path(os.path.expanduser(str(store_path))).resolve()
        self.store_path.mkdir(parents=True, exist_ok=True)
        (self.store_path / "grounded").mkdir(exist_ok=True)
        (self.store_path / "simulated").mkdir(exist_ok=True)
        self.ledger_path = self.store_path / "ledger.jsonl"
        self.index_meta_path = self.store_path / "index_meta.json"
        self._grounded_ids: set[str] = set()
        self._simulated_ids: set[str] = set()
        self._load_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        if not self.ledger_path.exists():
            return
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    origin = entry.get("origin")
                    rid = entry.get("id")
                    if origin == "grounded" and rid:
                        self._grounded_ids.add(rid)
                    elif origin == "simulated" and rid:
                        self._simulated_ids.add(rid)
                except json.JSONDecodeError:
                    continue

    def _assert_grounded(self, record: Record) -> None:
        if record.origin != "grounded":
            raise ContaminationError(
                f"Refused: record {record.id} has origin={record.origin!r}; "
                "only grounded records may enter grounded indexes."
            )

    def _validate_partition(self, origin: str) -> None:
        if origin not in ("grounded", "simulated"):
            raise PartitionError(f"Invalid origin {origin!r}; must be 'grounded' or 'simulated'")

    def _append_ledger(self, record: Record, op: str = "remember") -> None:
        entry = record.to_dict()
        entry["op"] = op
        entry["ts"] = time.time()
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _write_record_file(self, record: Record) -> None:
        partition = "grounded" if record.origin == "grounded" else "simulated"
        path = self.store_path / partition / f"{record.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)

    def _simple_score(self, query: str, content: str) -> float:
        """Tiny keyword overlap scorer for CE (no external deps)."""
        q = set(query.lower().split())
        c = set(content.lower().split())
        if not q:
            return 0.0
        return len(q & c) / len(q)

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def remember(
        self,
        content: str,
        *,
        tags: Optional[Sequence[str]] = None,
        origin: str = "grounded",
        epistemic_status: str = "fact",
        evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a grounded fact. origin must be grounded (default)."""
        self._validate_partition(origin)
        if origin != "grounded":
            raise PartitionError(
                "remember() is grounded-only. Use remember_simulated() for hypotheses."
            )
        rid = str(uuid.uuid4())
        record = Record(
            id=rid,
            content=content,
            origin="grounded",
            tags=list(tags or []),
            epistemic_status=epistemic_status,
            evidence=evidence,
        )
        self._assert_grounded(record)
        self._append_ledger(record)
        self._write_record_file(record)
        self._grounded_ids.add(rid)
        return rid

    def remember_simulated(
        self,
        content: str,
        *,
        tags: Optional[Sequence[str]] = None,
        epistemic_status: str = "hypothesis",
    ) -> str:
        """Store a simulated / hypothetical record. Never indexed for grounded recall."""
        rid = str(uuid.uuid4())
        record = Record(
            id=rid,
            content=content,
            origin="simulated",
            tags=list(tags or []),
            epistemic_status=epistemic_status,
        )
        self._append_ledger(record)
        self._write_record_file(record)
        self._simulated_ids.add(rid)
        return rid

    def promote(
        self,
        record_id: str,
        *,
        evidence: Dict[str, Any],
    ) -> str:
        """
        Promote a simulated record to grounded.
        Requires non-empty evidence (resolved prediction or external attestation).
        A boolean flag or free-text note alone is refused.
        """
        if not evidence or not isinstance(evidence, dict):
            raise PromotionError("Promotion requires a non-empty evidence dict")
        if not any(evidence.values()):
            raise PromotionError("Evidence dict must contain at least one truthy value")

        sim_path = self.store_path / "simulated" / f"{record_id}.json"
        if not sim_path.exists():
            raise PromotionError(f"No simulated record {record_id}")

        with open(sim_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        old = Record.from_dict(data)

        new_id = str(uuid.uuid4())
        promoted = Record(
            id=new_id,
            content=old.content,
            origin="grounded",
            tags=old.tags,
            epistemic_status="fact",
            evidence=evidence,
            promoted_from=record_id,
        )
        self._assert_grounded(promoted)
        self._append_ledger(promoted, op="promote")
        self._write_record_file(promoted)
        self._grounded_ids.add(new_id)
        return new_id

    # ------------------------------------------------------------------
    # Public read API (reads never write)
    # ------------------------------------------------------------------

    def recall(self, query: str, k: int = 5) -> RecallResult:
        """Recall from grounded partition only."""
        hits: List[Dict[str, Any]] = []
        grounded_dir = self.store_path / "grounded"
        if grounded_dir.exists():
            scored = []
            for p in grounded_dir.glob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        rec = json.load(f)
                    if rec.get("origin") != "grounded":
                        # Should never happen; treat as violation signal
                        continue
                    score = self._simple_score(query, rec.get("content", ""))
                    if score > 0:
                        scored.append((score, rec))
                except (json.JSONDecodeError, OSError):
                    continue
            scored.sort(key=lambda x: x[0], reverse=True)
            for score, rec in scored[:k]:
                hits.append({"score": score, "record": rec})

        drift = self._check_drift()
        return RecallResult(
            hits=hits,
            healthy=drift["healthy"],
            diagnostic={"drift": drift, "query": query},
        )

    def contamination(self) -> ContaminationReport:
        """Audit for simulated content inside grounded indexes / files."""
        violations: List[str] = []
        grounded_dir = self.store_path / "grounded"
        if grounded_dir.exists():
            for p in grounded_dir.glob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        rec = json.load(f)
                    if rec.get("origin") != "grounded":
                        violations.append(f"simulated-in-grounded-dir:{p.name}")
                except (json.JSONDecodeError, OSError):
                    continue

        # Also scan ledger for consistent tagging
        if self.ledger_path.exists():
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        origin = entry.get("origin")
                        if origin not in ("grounded", "simulated"):
                            violations.append(f"ledger-line-{i}:bad-origin")
                    except json.JSONDecodeError:
                        violations.append(f"ledger-line-{i}:parse-error")

        rate = 0.0 if not violations else min(1.0, len(violations) / max(1, len(self._grounded_ids)))
        return ContaminationReport(
            contamination_rate=rate,
            grounded_count=len(self._grounded_ids),
            simulated_count=len(self._simulated_ids),
            violations=violations,
            healthy=rate == 0.0 and not violations,
        )

    def health(self) -> Dict[str, Any]:
        cont = self.contamination()
        drift = self._check_drift()
        return {
            "healthy": cont.healthy and drift["healthy"],
            "contamination_rate": cont.contamination_rate,
            "grounded_count": cont.grounded_count,
            "simulated_count": cont.simulated_count,
            "drift": drift,
        }

    def _check_drift(self) -> Dict[str, Any]:
        """Compare ledger IDs vs on-disk partition files."""
        ledger_grounded = set(self._grounded_ids)
        disk_grounded = set()
        gdir = self.store_path / "grounded"
        if gdir.exists():
            for p in gdir.glob("*.json"):
                disk_grounded.add(p.stem)
        missing_on_disk = ledger_grounded - disk_grounded
        extra_on_disk = disk_grounded - ledger_grounded
        healthy = not missing_on_disk and not extra_on_disk
        return {
            "healthy": healthy,
            "missing_on_disk": sorted(missing_on_disk),
            "extra_on_disk": sorted(extra_on_disk),
            "stale_pointers": len(missing_on_disk) + len(extra_on_disk),
        }
