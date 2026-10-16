"""Git helpers for diffblast. Pure standard library, no network, no config."""
import os
import subprocess


def run_git(args, cwd):
    try:
        res = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return ""
    if res.returncode != 0:
        return ""
    return res.stdout


def find_repo_root(start):
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def resolve_base(repo):
    for b in ("origin/main", "origin/master", "main", "master"):
        if run_git(["rev-parse", "--verify", b], repo).strip():
            return b
    if run_git(["rev-parse", "-q", "--verify", "HEAD~1"], repo).strip():
        return "HEAD~1"
    return None


def get_changed_files(repo, base):
    """Return repo-relative changed files (uncommitted + committed vs base)."""
    changed = set()

    # Uncommitted (including untracked, staged, renamed).
    out = run_git(["status", "--porcelain", "-uall"], repo)
    for line in out.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:].strip()
        if " -> " in rest:  # rename: a -> b
            rest = rest.split(" -> ")[1]
        changed.add(rest.strip().strip('"'))

    # Committed changes vs base.
    if base:
        for spec in (f"{base}...HEAD", f"{base}", f"{base}..HEAD"):
            out = run_git(["diff", "--name-only", spec], repo)
            if out.strip():
                for f in out.splitlines():
                    if f.strip():
                        changed.add(f.strip())
                break

    return sorted(changed)


def get_tracked_files(repo):
    out = run_git(["ls-files"], repo)
    return [l for l in out.splitlines() if l.strip()]


def build_cochange_counts(repo, max_commits=300):
    """Mine git history for files frequently changed together."""
    out = run_git(
        ["log", f"--max-count={max_commits}", "--name-only", "--pretty=format:"],
        repo,
    )
    pairs = {}
    for block in out.split("\n\n"):
        files = [f.strip() for f in block.splitlines() if f.strip()]
        n = len(files)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = files[i], files[j]
                key = (a, b) if a < b else (b, a)
                pairs[key] = pairs.get(key, 0) + 1
    return pairs
