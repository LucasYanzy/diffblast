# Good first issues (create these on the repo after publish)

Label each with `good first issue`. These are scoped, low-risk, and great for newcomers.

---

### 1. Add PHP test-file detection
`diffblast/tests.py` detects tests for many languages but not PHP (e.g. `*Test.php`,
`tests/*.phpt`). Add patterns to `TEST_PATTERNS` and a fixture under `tests/fixtures/`.
**Skills:** regex, Python. **Files:** `tests.py`, `tests/test_diffblast.py`.

### 2. Better Rust module resolution
Rust `use crate::foo::bar` currently maps to `foo/bar` heuristically. Improve it using
`Cargo.toml` package name + module path so resolution is accurate for real crates.
**Skills:** Rust, Python. **Files:** `deps.py`, `graph.py`.

### 3. `--since <commit>` flag
Add a flag to limit the analyzed diff to changes since a given commit/ref (today only
compares against a base branch). Wire it through `cli.py` → `git_utils.get_changed_files`.
**Skills:** Python, argparse. **Files:** `cli.py`, `git_utils.py`.

### 4. JUnit XML output for CI
Add `--junit out.xml` that emits recommended tests as a JUnit report so CI systems can
display them. Reuse the JSON data shape in `report.py`.
**Skills:** Python, XML. **Files:** `report.py`, `cli.py`.

### 5. `--quiet` / CI mode
Add `--quiet` that prints only the recommended test paths (one per line), so it can be
piped directly: `pytest $(diffblast --quiet)`.
**Skills:** Python, CLI. **Files:** `cli.py`, `report.py`.
