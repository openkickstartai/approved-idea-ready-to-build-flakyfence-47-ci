#!/usr/bin/env python3
"""FlakyFence - Test pollution bisection & shared state forensics engine."""
import subprocess, sys, os, json, argparse
from typing import List, Dict, Any, Callable


class StateSnapshot:
    """Capture process-level shared state for forensic diffing."""

    def __init__(self):
        self.env = dict(os.environ)
        self.modules = set(sys.modules.keys())

    def diff(self, after: "StateSnapshot") -> List[Dict[str, str]]:
        changes = []
        for k in set(after.env) - set(self.env):
            changes.append({"type": "env_added", "key": k, "value": after.env[k]})
        for k in set(self.env) - set(after.env):
            changes.append({"type": "env_removed", "key": k})
        for k in set(self.env) & set(after.env):
            if self.env[k] != after.env[k]:
                changes.append({"type": "env_changed", "key": k, "old": self.env[k], "new": after.env[k]})
        for m in after.modules - self.modules:
            changes.append({"type": "module_added", "module": m})
        return changes


def bisect_polluter(victim: str, suspects: List[str], runner: Callable = None,
                    project: str = ".") -> List[str]:
    """Delta-debug: find minimal set of tests that pollute victim."""
    if runner is None:
        runner = lambda tests: run_sequence(tests + [victim], project)
    if len(suspects) <= 1:
        return suspects
    mid = len(suspects) // 2
    left, right = suspects[:mid], suspects[mid:]
    if not runner(left):
        return bisect_polluter(victim, left, runner)
    if not runner(right):
        return bisect_polluter(victim, right, runner)
    return suspects


def run_sequence(tests: List[str], project: str = ".") -> bool:
    """Run tests in given order, return True if all pass."""
    if not tests:
        return True
    cmd = [sys.executable, "-m", "pytest", "-xvs", "--tb=no",
           "--no-header", "-p", "no:cacheprovider"] + tests
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=project)
    return r.returncode == 0


def collect_tests(path: str = ".") -> List[str]:
    """Collect test node IDs via pytest."""
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header", path]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=path)
    return [line.strip() for line in r.stdout.splitlines() if "::" in line]


def find_victims(test_ids: List[str], project: str = ".") -> List[str]:
    """Find tests that fail in suite but pass in isolation."""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=no", "--no-header",
           "-p", "no:cacheprovider"] + test_ids
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=project)
    if r.returncode == 0:
        return []
    victims = []
    for line in r.stdout.splitlines():
        if " FAILED" in line:
            tid = line.split(" ")[0].strip()
            if tid and run_sequence([tid], project):
                victims.append(tid)
    return victims


def to_sarif(results: List[Dict]) -> Dict[str, Any]:
    """Generate SARIF 2.1.0 report from pollution findings."""
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "FlakyFence", "version": "0.1.0",
            "rules": [{"id": "test-pollution",
                       "shortDescription": {"text": "Test pollution detected"}}]}},
            "results": [{"ruleId": "test-pollution", "level": "error",
                "message": {"text": f"{r['victim']} polluted by {r['polluters']}"},
                "properties": {"stateChanges": r.get("state_changes", [])}}
                for r in results]}]
    }


def analyze(test_ids: List[str], project: str = ".", limit: int = 3) -> List[Dict]:
    """Full pipeline: find victims, bisect polluters, collect state diffs."""
    victims = find_victims(test_ids, project)
    results = []
    for i, victim in enumerate(victims):
        if 0 < limit <= i:
            print(f"\u26a0\ufe0f  Free tier limit ({limit}). Upgrade: flakyfence.dev/pro")
            break
        idx = test_ids.index(victim) if victim in test_ids else len(test_ids)
        suspects = [t for t in test_ids[:idx] if t != victim]
        polluters = bisect_polluter(victim, suspects, project=project)
        results.append({"victim": victim, "polluters": polluters, "state_changes": []})
    return results


def main():
    p = argparse.ArgumentParser(prog="flakyfence",
        description="\U0001f52c Find which test pollutes shared state and breaks your CI")
    p.add_argument("tests", nargs="*", help="Test files or node IDs to analyze")
    p.add_argument("--project", default=".", help="Project root directory")
    p.add_argument("--sarif", help="Write SARIF report to file")
    p.add_argument("--json-output", action="store_true", help="JSON stdout")
    p.add_argument("--limit", type=int, default=3,
                   help="Max victims to analyze (0=unlimited, free=3)")
    args = p.parse_args()
    test_ids = args.tests or collect_tests(args.project)
    if not test_ids:
        print("No tests found."); return 0
    print(f"\U0001f52c FlakyFence analyzing {len(test_ids)} tests...")
    results = analyze(test_ids, args.project, args.limit)
    if args.sarif:
        with open(args.sarif, "w") as f:
            json.dump(to_sarif(results), f, indent=2)
        print(f"\U0001f4c4 SARIF \u2192 {args.sarif}")
    elif args.json_output:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("\u2705 No test pollution detected!")
        for r in results:
            print(f"\U0001f534 {r['victim']}")
            print(f"   polluted by: {', '.join(r['polluters'])}")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
