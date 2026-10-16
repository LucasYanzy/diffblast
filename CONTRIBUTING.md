# Contributing to diffblast

diffblast is intentionally small and dependency-free so it's easy to hack on.

## Dev setup

```bash
git clone https://github.com/diffblast/diffblast
cd diffblast
pip install -e ".[test]"   # -e works without network; no third-party deps needed
pytest
```

## Architecture

- `diffblast/git_utils.py` — git calls (changed files, tracked files, co-change mining).
- `diffblast/deps.py` — per-language import/include extraction + local file resolution.
- `diffblast/graph.py` — dependency graph + blast-radius BFS.
- `diffblast/tests.py` — test-file detection and recommendation.
- `diffblast/report.py` — terminal / Markdown / JSON output.
- `diffblast/cli.py` — argument parsing + orchestration.

## Adding a language

1. Add the extension → language name in `LANG_BY_EXT` in `deps.py`.
2. Add an extractor `_<lang>()` that returns a list of raw import strings.
3. Make sure `resolve_local()` can map the raw import to a repo file (add heuristics if needed).
4. Add test fixtures under `tests/fixtures/` and a case in `tests/test_diffblast.py`.

## Guidelines

- Keep it dependency-free (Python stdlib only). No new third-party packages without discussion.
- Add a test for any behavior change.
- Run `pytest` and `python -m diffblast --help` before opening a PR.
- Good first issues are labeled `good first issue`.
