"""Detect test files and recommend which to run for a change set."""
import os
import re

TEST_PATTERNS = [
    r"^test_.*\.py$",
    r".*_test\.py$",
    r".*\.test\.(ts|tsx|js|jsx)$",
    r".*\.spec\.(ts|tsx|js|jsx)$",
    r".*_test\.go$",
    r".*_test\.rs$",
    r".*Test\.java$",
    r".*_test\.c(pp|xx|c)?$",
    r"test.*\.rb$",
    r".*Test\.cs$",
]


def is_test_file(path):
    base = os.path.basename(path)
    low_dir = os.path.dirname(path).lower()
    if "test" in low_dir and ("test" in base.lower() or "spec" in base.lower()):
        return True
    for p in TEST_PATTERNS:
        if re.match(p, base):
            return True
    return False


def detect_tests(tracked_set):
    return {f for f in tracked_set if is_test_file(f)}


def recommend_tests(impacted, test_set):
    recommended = sorted(t for t in impacted if t in test_set)
    # Heuristic source->test pairing for non-test impacted files.
    paired = []
    for f in impacted:
        if f in test_set:
            continue
        stem = os.path.splitext(os.path.basename(f))[0]
        if not stem:
            continue
        for t in test_set:
            tb = os.path.basename(t)
            if tb.startswith("test_" + stem) or tb.startswith(stem + "_test") \
               or tb.startswith(stem + ".test") or tb.startswith(stem + ".spec") \
               or tb.startswith(stem + "Test"):
                paired.append((f, t))
    return recommended, paired
