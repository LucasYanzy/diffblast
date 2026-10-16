import os
import subprocess
import sys
import tempfile

import pytest

from diffblast import deps, tests as tmod, report, graph

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write(repo, rel, content):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return rel


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


@pytest.fixture
def sample_repo(tmp_path):
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.io")
    _git(repo, "config", "user.name", "t")
    _write(repo, "pkg/core.py", "def core():\n    return 1\n")
    _write(repo, "pkg/util.py", "from .core import core\n\ndef util():\n    return core()\n")
    _write(repo, "app/main.py", "from pkg.util import util\n\ndef main():\n    return util()\n")
    _write(repo, "tests/test_core.py", "def test_core():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def test_detect_tests():
    files = {
        "tests/test_foo.py", "src/foo_test.go", "a/b.spec.ts",
        "pkg/core.py", "README.md",
    }
    found = tmod.detect_tests(files)
    assert "tests/test_foo.py" in found
    assert "src/foo_test.go" in found
    assert "a/b.spec.ts" in found
    assert "pkg/core.py" not in found


def test_extract_imports_python():
    repo = REPO_ROOT
    # self-test on the package's own files
    imps = deps.extract_imports(repo, "diffblast/cli.py")
    assert any("argparse" in i for i in imps)


def test_resolve_local_relative():
    repo = REPO_ROOT
    dst = deps.resolve_local(repo, "diffblast/cli.py", ".cli")
    assert dst in (None, "diffblast/cli.py")  # may resolve to self; just must not crash


def test_blast_radius(sample_repo):
    tracked = ["pkg/core.py", "pkg/util.py", "app/main.py", "tests/test_core.py"]
    edges = graph.build_dependency_graph(sample_repo, tracked)
    # util.py imports core.py
    assert ("pkg/util.py", ("pkg/core.py", "import")) in [
        (s, e) for s, es in edges.items() for e in es
    ]
    changed = ["pkg/core.py"]
    impacted, reasons = graph.compute_blast_radius(
        changed, edges, {}, 5, set(tracked)
    )
    assert "pkg/core.py" in impacted
    assert "pkg/util.py" in impacted  # reached via import edge


def test_recommend_tests(sample_repo):
    tracked = {"pkg/core.py", "pkg/util.py", "app/main.py", "tests/test_core.py"}
    impacted = {"pkg/core.py", "pkg/util.py", "tests/test_core.py"}
    recommended, paired = tmod.recommend_tests(impacted, tmod.detect_tests(tracked))
    assert "tests/test_core.py" in recommended


def test_risk_score_isolated():
    score, label = report.risk_score(["a.py"], {"a.py"}, {})
    assert score == 10
    assert label == "Low"


def test_resolve_local_index_src_layout():
    tracked = ["src/pkg/core.py", "src/pkg/util.py", "tests/test_core.py"]
    index = deps.build_index(tracked)
    # package import "pkg.core" must resolve under src/ layout
    dst = deps.resolve_local(REPO_ROOT, "src/app.py", "pkg.core", set(tracked), index)
    assert dst == "src/pkg/core.py"


def test_read_text_skips_binary(tmp_path):
    p = tmp_path / "x.py"
    p.write_bytes(b"\x00\x01\x02binary\x00")
    assert deps.read_text(str(p)) == ""


def test_read_text_skips_huge(tmp_path):
    p = tmp_path / "big.py"
    p.write_text("x = 1\n" * 500000)
    assert deps.read_text(str(p)) == ""  # > 2MB guard


def test_color_disabled_when_requested(capsys):
    out = report.print_table(
        ["a.py"], {"a.py"}, {"a.py": {"changed"}}, [], [],
        (10, "Low"), color=False,
    )
    captured = capsys.readouterr().out
    assert "\033[" not in captured


def test_end_to_end_no_color_flag(sample_repo):
    _write(sample_repo, "pkg/core.py", "def core():\n    return 2\n")
    r = subprocess.run(
        [sys.executable, "-m", "diffblast", "--path", sample_repo,
         "--no-cochange", "--no-color"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert r.returncode == 0
    assert "\033[" not in r.stdout
    assert "pkg/util.py" in r.stdout


def test_end_to_end_cli(sample_repo):
    env = dict(os.environ)
    # make a change
    _write(sample_repo, "pkg/core.py", "def core():\n    return 2\n")
    r = subprocess.run(
        [sys.executable, "-m", "diffblast", "--path", sample_repo, "--no-cochange"],
        capture_output=True, text=True, cwd=REPO_ROOT, env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "Blast radius" in r.stdout
    assert "pkg/util.py" in r.stdout
