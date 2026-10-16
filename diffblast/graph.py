"""Build dependency + co-change graphs and compute blast radius."""
from . import deps, git_utils


def build_dependency_graph(repo_root, tracked):
    tracked_set = set(tracked)
    index = deps.build_index(tracked)
    edges = {}  # src -> list of (dst, "import")
    for f in tracked:
        for raw in deps.extract_imports(repo_root, f):
            dst = deps.resolve_local(repo_root, f, raw, tracked_set, index)
            if dst and dst in tracked_set and dst != f:
                edges.setdefault(f, []).append((dst, "import"))
    return edges


def compute_blast_radius(changed, dep_edges, cochange, co_threshold, tracked_set):
    # Reverse dependency map: dst -> [(src, reason)] = "who depends on dst".
    dependents = {}
    for src, es in dep_edges.items():
        for dst, reason in es:
            dependents.setdefault(dst, []).append((src, reason))

    visited = set(changed)
    reasons = {f: {"changed"} for f in changed}
    queue = list(changed)

    while queue:
        node = queue.pop()
        for src, reason in dependents.get(node, []):
            if src not in visited:
                visited.add(src)
                reasons[src] = {reason}
                queue.append(src)
            else:
                reasons.setdefault(src, set()).add(reason)

    if co_threshold and cochange:
        co_by_file = {}
        for (a, b), w in cochange.items():
            co_by_file.setdefault(a, []).append((b, w))
            co_by_file.setdefault(b, []).append((a, w))
        for node in list(visited):
            for other, w in co_by_file.get(node, []):
                if w >= co_threshold and other in tracked_set and other not in visited:
                    visited.add(other)
                    reasons[other] = {"co-change"}

    return visited, reasons
