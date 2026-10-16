# diffblast

> **Know exactly what your change breaks — before you push.**
> Compute the blast radius of your git changes and get a precise list of which tests to run. Zero config, zero dependencies, runs fully offline in seconds.

---

## Why

You touch `src/core/math.py`. Does it break `checkout`? `pricing`? Some test three packages away?
Running the whole suite is slow; guessing is risky. `diffblast` traces your change through the
real dependency graph **and** your git history, then tells you exactly what's impacted and which
tests actually matter.

```text
$ diffblast
diffblast — change blast radius

Changed files : 1
Blast radius  : 5 files
Tests to run  : 2
Risk          : Medium (26/100)

Changed
  • src/core/math.py

Impacted (beyond what you touched)
  • src/app.py          [import]
  • src/utils/calc.py   [import]
  • tests/test_math.py  [import]
  • tests/test_calc.py  [import]

Recommended tests
  ✓ tests/test_calc.py
  ✓ tests/test_math.py
```

---

## Install

One command, no dependencies, no network:

```bash
pip install diffblast
```

Or run it without installing (Python ≥ 3.8 already on your machine):

```bash
python -m diffblast
```

(Clone first: `git clone https://github.com/diffblast/diffblast && cd diffblast && pip install -e .`)

---

## Usage

Run inside any git repo after you've made changes:

```bash
diffblast                 # analyze working tree vs auto-detected base branch
diffblast --base main     # compare against a specific branch
diffblast --json          # machine-readable output for CI
diffblast --md --out report.md   # save a Markdown report
diffblast --no-cochange   # skip git-history mining (fastest)
```

Works on uncommitted changes **and** committed changes on your branch vs `main`.

---

## How it works

1. **Changed files** — from `git status` (uncommitted) + `git diff` vs your base branch.
2. **Dependency graph** — per-language import/include extraction (Python, JS/TS, Go, Rust,
   Java, C/C++, Ruby, PHP, C#) resolved to real repo files.
3. **Co-change graph** — mined from `git log`: files that keep changing together are treated
   as weakly coupled.
4. **Blast radius** — reverse BFS from your changed files over the dependency + co-change
   graph. Every file reached is something your change can break.
5. **Test recommendation** — test files inside the blast radius, plus name-based
   source→test pairing.

No LLM, no server, no data leaves your machine.

---

## Features

- 🔍 **Precise impact** — follows real imports, not just file names.
- 🧪 **Test targeting** — run only the tests that can actually fail.
- 🕰️ **History-aware** — `git log` co-change detection catches what static analysis misses.
- 📦 **Multi-language** — Python, JS/TS, Go, Rust, Java, C/C++, Ruby, PHP, C#.
- 🚀 **CI-ready** — `--json` output pipes straight into your pipeline.
- 🪶 **Zero dependencies** — pure Python stdlib; installs anywhere instantly.
- 🔒 **Private by default** — everything runs locally, offline.

---

## Comparison

| Tool | Scope | Depends on LLM | Config | Local-only | Deps |
|------|-------|---------------|--------|------------|------|
| **diffblast** | Blast radius + test targeting | No | None | Yes | 0 |
| `git diff` | Changed files only | No | None | Yes | 0 |
| IDE "find usages" | Manual, per-symbol | No | IDE | Yes | heavy |
| Generic impact tools | Single ecosystem / heavy setup | Often | Yes | Varies | many |
| "run all tests" | Whole suite | No | None | Yes | 0 |

---

## FAQ

**Does it need an LLM or API key?** No. It's pure static + git-history analysis.

**Does it upload my code?** Never. Everything runs locally.

**My language isn't detected well.** Resolution is heuristic (import paths). Open an issue or
PR — adding a language is ~20 lines (see `CONTRIBUTING.md`).

**What's the "Risk" score?** A 0–100 heuristic from blast-radius spread and co-change density:
`Low` (<25), `Medium` (<60), `High` (≥60). It's a nudge, not a guarantee.

**Does it work on huge repos?** Yes; history mining is capped (`--max-commits`, default 300)
and dependency extraction is file-by-file.

---

## Roadmap

- [ ] VS Code / Cursor extension (inline blast radius on save)
- [ ] Pre-commit hook mode (`diffblast --hook` fails CI if risky files untested)
- [ ] More languages & build-system-aware resolution (Bazel, monorepos)
- [ ] SARIF / JUnit output for CI dashboards
- [ ] Optional LLM explainer (`--explain`, off by default)

---

## License

[MIT](LICENSE)
