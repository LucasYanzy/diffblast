# Demo

Real output from `diffblast` run inside a small sample repo after editing
`src/core/math.py` (a function other modules and tests depend on).

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

### What this shows
- `src/core/math.py` was changed (1 file).
- `diffblast` followed `import` edges (`calc` → `math`, `app` → `calc`) and found
  **5 files** in the blast radius — without you having to know the dependency tree.
- It recommends the **2 tests** that can actually fail, so you skip the rest of the suite.

### Reproduce
```bash
git clone https://github.com/diffblast/diffblast
cd diffblast
pip install -e .
# make a change in any file of your own repo, then:
diffblast
```

A recorded terminal session (asciinema) will be added here on publish.
