# Reproduce the demo

Run `python3 scripts/demo.py` from the repository root. It builds a temporary Git repository with synthetic Python source and tests, makes real commits, edits two files, and invokes the actual CLI. No personal repository is read.

The captured output is in [terminal.txt](terminal.txt). Impact recommendations are heuristic and do not prove that unlisted tests are safe to skip.
