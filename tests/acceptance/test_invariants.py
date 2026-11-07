"""
Acceptance tests for mem20-ce Core Edition.

These must all pass before any release is called done.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mem20_ce import MemoryEngine
from mem20_ce.engine import ContaminationError, PartitionError, PromotionError


@pytest.fixture
def engine(tmp_path):
    return MemoryEngine(store_path=tmp_path / "store")


def test_remember_is_grounded_only(engine):
    rid = engine.remember("deploy key rotates Monday", tags=["ops"])
    assert rid
    with pytest.raises(PartitionError):
        engine.remember("this is a hypothesis", origin="simulated")


def test_simulated_never_in_grounded_index(engine):
    engine.remember("real fact about production")
    engine.remember_simulated("hypothetical: production is down")

    res = engine.recall("production")
    for hit in res.hits:
        assert hit["record"]["origin"] == "grounded"
        assert "hypothetical" not in hit["record"]["content"].lower()

    # Direct filesystem check
    gdir = Path(engine.store_path) / "grounded"
    for p in gdir.glob("*.json"):
        data = json.loads(p.read_text())
        assert data["origin"] == "grounded"


def test_contamination_rate_zero_on_clean_store(engine):
    engine.remember("grounded A")
    engine.remember_simulated("simulated B")
    engine.remember("grounded C")
    report = engine.contamination()
    assert report.contamination_rate == 0.0
    assert report.healthy is True
    assert report.violations == []


def test_promotion_requires_evidence(engine):
    sid = engine.remember_simulated("maybe the key was rotated")
    with pytest.raises(PromotionError):
        engine.promote(sid, evidence={})
    with pytest.raises(PromotionError):
        engine.promote(sid, evidence={"note": ""})

    new_id = engine.promote(sid, evidence={"resolved_prediction": True, "attestation": "ops-bot"})
    assert new_id
    res = engine.recall("key was rotated")
    assert any(h["record"]["id"] == new_id for h in res.hits)


def test_reads_never_write_ledger(engine):
    engine.remember("stable fact")
    before = engine.ledger_path.read_text() if engine.ledger_path.exists() else ""
    engine.recall("stable")
    engine.contamination()
    engine.health()
    after = engine.ledger_path.read_text() if engine.ledger_path.exists() else ""
    assert before == after


def test_index_drift_is_detectable(engine):
    rid = engine.remember("fact for drift test")
    # Manually create drift: remove the grounded file but leave ledger entry
    gfile = Path(engine.store_path) / "grounded" / f"{rid}.json"
    assert gfile.exists()
    gfile.unlink()
    drift = engine._check_drift()
    assert drift["healthy"] is False
    assert rid in drift["missing_on_disk"]
    health = engine.health()
    assert health["healthy"] is False


def test_recall_healthy_flag(engine):
    engine.remember("alpha")
    res = engine.recall("alpha")
    assert res.healthy is True
    assert len(res.hits) >= 1
