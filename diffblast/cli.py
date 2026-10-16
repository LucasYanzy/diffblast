"""diffblast command-line interface."""
import argparse
import os
import sys

from . import git_utils, graph, report, tests
from .__init__ import __version__


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="diffblast",
        description="Compute the blast radius of your git changes and "
                    "recommend which tests to run — before you push.",
    )
    p.add_argument(
        "--base", default=None,
        help="Base branch/ref to diff against (default: auto-detect origin/main).",
    )
    p.add_argument("--path", default=None, help="Path to a git repository (default: cwd).")
    p.add_argument("--json", action="store_true", help="Output JSON.")
    p.add_argument("--md", action="store_true", help="Output Markdown report.")
    p.add_argument("--out", default=None, help="Write report to this file instead of stdout.")
    p.add_argument(
        "--co-threshold", type=int, default=5,
        help="Co-change weight (commits changed together) to count as influence (default 5).",
    )
    p.add_argument(
        "--max-commits", type=int, default=300,
        help="Number of git history commits to mine for co-change (default 300).",
    )
    p.add_argument("--no-cochange", action="store_true", help="Disable git history mining.")
    p.add_argument("--no-color", action="store_true", help="Disable colored output (auto-off when piped).")
    p.add_argument("--version", action="version", version=f"diffblast {__version__}")
    return p.parse_args(argv)


def run(args):
    cwd = os.path.abspath(args.path) if args.path else os.getcwd()
    repo = git_utils.find_repo_root(cwd)
    if not repo:
        sys.stderr.write("diffblast: not a git repository (use --path)\n")
        return 1

    base = args.base or git_utils.resolve_base(repo)
    tracked = git_utils.get_tracked_files(repo)
    tracked_set = set(tracked)

    changed = git_utils.get_changed_files(repo, base)
    if not changed:
        sys.stderr.write(
            "diffblast: no changes detected. "
            "Make some changes or pass --base <branch>.\n"
        )
        return 0

    dep_edges = graph.build_dependency_graph(repo, tracked)
    cochange = {}
    if not args.no_cochange:
        cochange = git_utils.build_cochange_counts(repo, args.max_commits)

    impacted, reasons = graph.compute_blast_radius(
        changed, dep_edges, cochange, args.co_threshold, tracked_set
    )
    test_set = tests.detect_tests(tracked_set)
    recommended, paired = tests.recommend_tests(impacted, test_set)
    risk = report.risk_score(changed, impacted, cochange)

    if args.json:
        text = report.to_json(changed, impacted, reasons, recommended, paired, risk, base)
    elif args.md:
        text = report.to_markdown(changed, impacted, reasons, recommended, paired, risk, base)
    else:
        color = bool(sys.stdout.isatty()) and not os.environ.get("NO_COLOR") and not args.no_color
        report.print_table(changed, impacted, reasons, recommended, paired, risk, color=color)
        text = None

    if text is not None:
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        else:
            print(text)
    return 0


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    return run(args)
