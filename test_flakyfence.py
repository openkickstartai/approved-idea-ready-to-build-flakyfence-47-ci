"""Tests for FlakyFence core engine."""
import os, sys, json
from flakyfence import StateSnapshot, bisect_polluter, to_sarif


def test_snapshot_detects_env_addition():
    before = StateSnapshot()
    os.environ["_FLAKYFENCE_TEST_ADD"] = "dirty_value"
    after = StateSnapshot()
    del os.environ["_FLAKYFENCE_TEST_ADD"]
    changes = before.diff(after)
    added = [c for c in changes if c.get("key") == "_FLAKYFENCE_TEST_ADD"]
    assert len(added) == 1
    assert added[0]["type"] == "env_added"
    assert added[0]["value"] == "dirty_value"


def test_snapshot_detects_env_change():
    os.environ["_FF_MUT"] = "original"
    before = StateSnapshot()
    os.environ["_FF_MUT"] = "mutated"
    after = StateSnapshot()
    del os.environ["_FF_MUT"]
    changes = before.diff(after)
    changed = [c for c in changes if c.get("key") == "_FF_MUT"]
    assert len(changed) == 1
    assert changed[0]["type"] == "env_changed"
    assert changed[0]["old"] == "original"
    assert changed[0]["new"] == "mutated"


def test_snapshot_detects_env_removal():
    os.environ["_FF_DEL"] = "exists"
    before = StateSnapshot()
    del os.environ["_FF_DEL"]
    after = StateSnapshot()
    changes = before.diff(after)
    removed = [c for c in changes if c.get("key") == "_FF_DEL"]
    assert len(removed) == 1
    assert removed[0]["type"] == "env_removed"


def test_snapshot_detects_module_leak():
    before = StateSnapshot()
    after = StateSnapshot()
    after.modules.add("_fake_leaked_module_xyz")
    changes = before.diff(after)
    mods = [c for c in changes if c.get("module") == "_fake_leaked_module_xyz"]
    assert len(mods) == 1
    assert mods[0]["type"] == "module_added"


def test_snapshot_no_changes():
    snap = StateSnapshot()
    assert snap.diff(snap) == []


def test_bisect_finds_single_polluter():
    runner = lambda tests: "test_b" not in tests
    result = bisect_polluter("victim", ["test_a", "test_b", "test_d"], runner=runner)
    assert result == ["test_b"]


def test_bisect_single_suspect():
    result = bisect_polluter("victim", ["only"], runner=lambda t: False)
    assert result == ["only"]


def test_bisect_empty_suspects():
    result = bisect_polluter("victim", [], runner=lambda t: True)
    assert result == []


def test_bisect_needs_both_halves():
    """When pollution requires two tests together."""
    runner = lambda t: not ("a" in t and "b" in t)
    result = bisect_polluter("victim", ["a", "b"], runner=runner)
    assert set(result) == {"a", "b"}


def test_bisect_polluter_at_end_of_large_list():
    suspects = [f"t{i}" for i in range(16)]
    runner = lambda tests: "t14" not in tests
    result = bisect_polluter("victim", suspects, runner=runner)
    assert result == ["t14"]


def test_sarif_valid_structure():
    findings = [{"victim": "test_a.py::test_x",
                 "polluters": ["test_a.py::test_y"],
                 "state_changes": [{"type": "env_added", "key": "DB"}]}]
    sarif = to_sarif(findings)
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["tool"]["driver"]["name"] == "FlakyFence"
    assert len(sarif["runs"][0]["results"]) == 1
    r = sarif["runs"][0]["results"][0]
    assert r["ruleId"] == "test-pollution"
    assert r["level"] == "error"
    assert "test_x" in r["message"]["text"]


def test_sarif_empty_results():
    sarif = to_sarif([])
    assert sarif["runs"][0]["results"] == []
    assert sarif["version"] == "2.1.0"
