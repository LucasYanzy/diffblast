"""Language-aware import/include extraction -> best-effort local file resolution."""
import os
import re
import ast

LANG_BY_EXT = {
    ".py": "python", ".pyi": "python",
    ".js": "js", ".jsx": "js", ".ts": "ts", ".tsx": "ts", ".mjs": "js", ".cjs": "js",
    ".go": "go", ".rs": "rust", ".java": "java",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    ".rb": "ruby", ".php": "php", ".cs": "csharp",
}

EXTS = [".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java",
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".rb", ".php", ".cs"]

MAX_FILE_BYTES = 2_000_000


def language_of(path):
    return LANG_BY_EXT.get(os.path.splitext(path)[1].lower())


def _stem_of(path):
    s = path
    for e in EXTS:
        if s.endswith(e):
            s = s[: -len(e)]
            break
    return s


def read_text(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        return ""
    if size == 0 or size > MAX_FILE_BYTES:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    except OSError:
        return ""
    if "\x00" in data[:8192]:  # almost certainly a binary file
        return ""
    return data


def extract_imports(repo_root, path):
    lang = language_of(path)
    text = read_text(os.path.join(repo_root, path))
    if not text:
        return []
    if lang == "python":
        return _py(text)
    if lang in ("js", "ts"):
        return _js(text)
    if lang == "go":
        return _go(text)
    if lang == "rust":
        return _rust(text)
    if lang == "java":
        return _java(text)
    if lang in ("c", "cpp"):
        return _c(text)
    return _generic(text)


def _py(text):
    out = []
    try:
        tree = ast.parse(text)
    except Exception:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                out.append("." * node.level + (node.module or ""))
            elif node.module:
                out.append(node.module)
    return out


def _js(text):
    out = []
    for m in re.finditer(r'import\s+[^;]*?\bfrom\s+[\'"]([^\'"]+)[\'"]', text):
        out.append(m.group(1))
    for m in re.finditer(r'(?:require|import)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', text):
        out.append(m.group(1))
    return out


def _go(text):
    out = []
    for m in re.finditer(r'import\s+[\'"]([^\'"]+)[\'"]', text):
        out.append(m.group(1))
    for m in re.finditer(r'import\s*\(([\s\S]*?)\)', text):
        for mm in re.finditer(r'[\'"]([^\'"]+)[\'"]', m.group(1)):
            out.append(mm.group(1))
    return out


def _rust(text):
    out = []
    for m in re.finditer(r'(?:use|mod)\s+([\w:]+)', text):
        out.append(m.group(1).replace("::", "/"))
    return out


def _java(text):
    out = []
    for m in re.finditer(r'import\s+([\w.]+)\s*;', text):
        out.append(m.group(1).replace(".", "/"))
    return out


def _c(text):
    out = []
    for m in re.finditer(r'#include\s+["<]([^">]+)[">]', text):
        out.append(m.group(1))
    return out


def _generic(text):
    out = []
    for m in re.finditer(r'(?:import|include|require|from)\s+[\'"]([^\'"]+)[\'"]', text):
        out.append(m.group(1))
    return out


def build_index(tracked):
    """Precompute module-stem and leaf-stem indexes for fast resolution."""
    stem_index = {}
    leaf_index = {}
    for f in tracked:
        s = _stem_of(f)
        stem_index[s] = f
        leaf = s.split("/")[-1]
        leaf_index.setdefault(leaf, []).append(f)
    return {"stem": stem_index, "leaf": leaf_index}


def resolve_local(repo_root, importer, raw, tracked_set=None, index=None):
    """Resolve an imported name to a repo-relative file path, or None."""
    importer_dir = os.path.dirname(importer)
    if raw.startswith("."):
        level = len(raw) - len(raw.lstrip("."))
        rest = raw[level:].replace(".", "/")
        pkg_dir = importer_dir
        for _ in range(level - 1):
            pkg_dir = os.path.dirname(pkg_dir)
        if not rest:
            target = pkg_dir
        else:
            target = os.path.normpath(os.path.join(pkg_dir, rest))
        return _find_existing(repo_root, target)

    norm = raw.replace("::", "/").replace(".", "/").lstrip("/")
    if not norm:
        return None

    if index is not None:
        exact = index["stem"].get(norm)
        if exact:
            return exact
        leaf = norm.split("/")[-1]
        for cand in index["leaf"].get(leaf, []):
            s = _stem_of(cand)
            if s == norm or s.endswith("/" + norm):
                return cand
        return None

    if tracked_set is not None:
        for t in tracked_set:
            s = _stem_of(t)
            if s == norm or s.endswith("/" + norm):
                return t
        return None

    target = os.path.normpath(os.path.join(repo_root, norm))
    return _find_existing(repo_root, target)


def _find_existing(repo_root, target):
    target = target.replace("\\", "/")
    cands = [target + e for e in EXTS]
    cands.append(target + "/__init__.py")
    for e in EXTS:
        cands.append(target + "/index" + e)
    for c in cands:
        if os.path.isfile(os.path.join(repo_root, c)):
            return c.replace("\\", "/")
    return None
