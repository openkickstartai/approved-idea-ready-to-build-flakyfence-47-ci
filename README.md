# 🔬 FlakyFence

**Stop re-running CI. Find the test that broke yours.**

FlakyFence automatically bisects your test suite to pinpoint exactly which test pollutes shared state and causes flaky failures. Delta-debugging finds the culprit in O(log n) runs instead of you staring at logs for hours.

## 🚀 Quick Start

```bash
pip install flakyfence

# Analyze all tests in current project
flakyfence

# Analyze specific tests
flakyfence tests/test_api.py tests/test_models.py

# Output SARIF for GitHub Code Scanning
flakyfence --sarif report.sarif

# JSON output for CI pipelines
flakyfence --json-output

# Pro: unlimited analysis
flakyfence --limit 0
```

## How It Works

1. **Detect victims** — finds tests that fail in suite but pass alone
2. **Bisect polluters** — delta-debugging narrows 500 suspects → 1 polluter in ~9 runs
3. **State forensics** — reports what shared state was mutated (env vars, modules, globals)
4. **Report** — terminal, JSON, or SARIF output

## 📊 Why Pay for FlakyFence?

| Pain | Cost without FlakyFence | With FlakyFence |
|------|------------------------|----------------|
| Dev debugging flaky test | 2-8 hours ($200-800) | 30 seconds |
| CI re-runs per month | 50+ wasted runs ($150+) | 0 |
| Team frustration | Priceless | Gone |

> A single flaky test costs teams **$500+/month** in wasted CI and developer time.

## 💰 Pricing

| Feature | Free | Pro $29/mo | Enterprise |
|---------|------|-----------|------------|
| Bisection engine | ✅ 3 victims/run | ✅ Unlimited | ✅ Unlimited |
| State forensics | env vars only | Full (env, modules, globals, DB) | Full + custom hooks |
| SARIF reports | ❌ | ✅ | ✅ |
| GitHub Action | ❌ | ✅ | ✅ |
| Django/SQLAlchemy support | ❌ | ✅ | ✅ |
| Async state tracking | ❌ | ✅ | ✅ |
| Priority support | ❌ | Email | Slack + SLA |
| SSO / audit log | ❌ | ❌ | ✅ |
| Price | $0 | $29/mo | Custom |

## CI Integration

```yaml
# .github/workflows/flaky.yml
- uses: actions/setup-python@v5
- run: pip install flakyfence
- run: flakyfence --sarif flaky.sarif || true
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: flaky.sarif
```

## License

MIT (core) — Pro features require a license key.
