"""Output formatting: terminal table, Markdown, JSON."""
import json


def risk_score(changed, impacted, cochange):
    spread = len(impacted) - len(changed)
    pair_count = sum(1 for w in (cochange or {}).values() if w >= 2)
    score = 10 + spread * 4 + min(pair_count, 20)
    score = max(0, min(100, score))
    label = "Low" if score < 25 else ("Medium" if score < 60 else "High")
    return score, label


def _color(text, code):
    return f"\033[{code}m{text}\033[0m"


def print_table(changed, impacted, reasons, recommended, paired, risk, color=True):
    c = (lambda t, code: t) if not color else _color
    score, label = risk
    print(c("diffblast", "1;36") + " — change blast radius\n")
    print(f"Changed files : {len(changed)}")
    print(f"Blast radius  : {len(impacted)} files")
    print(f"Tests to run  : {len(recommended)}")
    risk_color = "1;31" if label == "High" else ("1;33" if label == "Medium" else "1;32")
    print(f"Risk          : {c(label, risk_color)} ({score}/100)\n")

    print(c("Changed", "1;33"))
    for f in changed:
        print(f"  • {f}")
    print()
    print(c("Impacted (beyond what you touched)", "1;36"))
    extras = [f for f in impacted if f not in changed]
    if not extras:
        print("  (none — change is isolated)")
    for f in extras:
        r = ",".join(sorted(reasons.get(f, set()) - {"changed"})) or "changed"
        print(f"  • {f}  [{c(r, '2')}]")
    print()
    if recommended:
        print(c("Recommended tests", "1;32"))
        for t in recommended:
            print(f"  ✓ {t}")
        print()
    if paired:
        print(c("Likely-related tests (by name)", "1;35"))
        for src, t in paired:
            print(f"  {src} -> {t}")
        print()


def to_markdown(changed, impacted, reasons, recommended, paired, risk, base):
    score, label = risk
    lines = ["# diffblast report", ""]
    lines.append(f"- Base branch: `{base or 'working tree'}`")
    lines.append(f"- Changed files: **{len(changed)}**")
    lines.append(f"- Blast radius: **{len(impacted)}** files")
    lines.append(f"- Tests to run: **{len(recommended)}**")
    lines.append(f"- Risk: **{label} ({score}/100)**")
    lines.append("")
    lines.append("## Changed")
    for f in changed:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("## Impacted (beyond what you touched)")
    extras = [f for f in impacted if f not in changed]
    if not extras:
        lines.append("- (none — change is isolated)")
    for f in extras:
        r = ",".join(sorted(reasons.get(f, set()) - {"changed"})) or "changed"
        lines.append(f"- `{f}` — _{r}_")
    lines.append("")
    if recommended:
        lines.append("## Recommended tests")
        for t in recommended:
            lines.append(f"- [ ] `{t}`")
        lines.append("")
    if paired:
        lines.append("## Likely-related tests (by name)")
        for src, t in paired:
            lines.append(f"- `{src}` -> `{t}`")
        lines.append("")
    return "\n".join(lines)


def to_json(changed, impacted, reasons, recommended, paired, risk, base):
    score, label = risk
    extras = [f for f in impacted if f not in changed]
    return json.dumps({
        "base": base,
        "changed": changed,
        "blast_radius": sorted(impacted),
        "impacted_extra": extras,
        "reasons": {f: sorted(reasons.get(f, set())) for f in impacted},
        "recommended_tests": recommended,
        "paired_tests": [{"source": s, "test": t} for s, t in paired],
        "risk": {"score": score, "label": label},
    }, indent=2)
