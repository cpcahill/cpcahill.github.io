#!/usr/bin/env python3
"""
Regenerate the site's scoring profile from Pathfinder's profile.yaml.

Why this exists
---------------
The demo on the site runs a JavaScript port of the Python scoring engine. The
logic is easy to keep honest, because it barely changes. The *data* is not: the
city list, the skill aliases and the signal phrases get edited often, and a
hand-copied duplicate drifts within a week. Once it drifts, the page is making
a claim about the app that is no longer true.

So the JavaScript object is generated, not written. profile.yaml stays the only
place any of this is defined.

Usage
-----
    python3 build_profile.py                    # assumes ../ProjectPathfinder
    python3 build_profile.py path/to/profile.yaml
    python3 build_profile.py --check            # exit 1 if regeneration is needed

The last form is what you want in CI, or as a pre-commit hook: it changes
nothing and simply fails if index.html is out of date.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("This script needs PyYAML. Install it with: pip install pyyaml")

HERE = Path(__file__).resolve().parent
DEFAULT_YAML = HERE.parent / "ProjectPathfinder" / "profile.yaml"
INDEX = HERE / "index.html"

BEGIN = "/* --- BEGIN GENERATED"
END = "/* --- END GENERATED"


# ---------------------------------------------------------------------------
# Formatting helpers
#
# The generated block is read by anyone who opens View Source on a portfolio
# site, so it is worth emitting something a person would be happy to read
# rather than one enormous minified line.
# ---------------------------------------------------------------------------

def js(value) -> str:
    """A JSON value with single-quoted strings, matching the file's style."""
    dumped = json.dumps(value, ensure_ascii=False)
    # json gives double quotes; swap to single quotes for consistency with the
    # rest of the script, escaping any apostrophes that appear inside strings.
    out, in_string, result = dumped, False, []
    i = 0
    while i < len(out):
        ch = out[i]
        if ch == '"':
            in_string = not in_string
            result.append("'")
        elif ch == "'" and in_string:
            result.append("\\'")
        elif ch == "\\" and i + 1 < len(out) and out[i + 1] == '"':
            result.append('"')
            i += 2
            continue
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def wrap_list(items: list[str], indent: int, width: int = 96) -> str:
    """Lay a list of rendered items out over as few lines as fit."""
    pad = " " * indent
    lines, current = [], pad
    for item in items:
        candidate = f"{item}, "
        if len(current) + len(candidate) > width and current.strip():
            lines.append(current.rstrip())
            current = pad
        current += candidate
    if current.strip():
        lines.append(current.rstrip().rstrip(","))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The generator
# ---------------------------------------------------------------------------

def build(profile: dict) -> str:
    sen = profile["seniority"]
    loc = profile["location"]
    comp = profile["compensation"]
    ind = profile["industries"]
    hf = profile["hard_filters"]
    sig = profile["signals"]

    out: list[str] = []
    add = out.append

    add("const PROFILE = {")

    # weights ---------------------------------------------------------------
    weights = ", ".join(f"{k}: {v}" for k, v in profile["weights"].items())
    add(f"  weights: {{ {weights} }},")
    add("")

    # seniority -------------------------------------------------------------
    add("  seniority: {")
    add(f"    maxYears: {sen['max_years_required']},")
    add("    excluded: [")
    add(wrap_list([js(str(t)) for t in sen["excluded_title_tokens"]], 14))
    add("    ],")
    add("    preferred: [")
    add(wrap_list([js(str(t)) for t in sen["preferred_title_tokens"]], 14))
    add("    ]")
    add("  },")
    add("")

    # role families ---------------------------------------------------------
    add("  families: [")
    fams = sorted(profile["role_families"].items(),
                  key=lambda kv: -float(kv[1].get("weight", 0)))
    for _key, fam in fams:
        label = js(fam.get("label", _key))
        weight = float(fam.get("weight", 0.5))
        titles = ", ".join(js(t.lower()) for t in fam.get("titles", []))
        add(f"    {{ label: {label}, weight: {weight:.2f}, titles: [{titles}] }},")
    out[-1] = out[-1].rstrip(",")
    add("  ],")
    add("")

    # skills ----------------------------------------------------------------
    add("  skills: [")
    for s in profile["skills"]:
        aliases = ", ".join(js(str(a).lower()) for a in s.get("aliases", []))
        add(f"    {{ name: {js(s['name'])}, tier: {js(s.get('tier', 'working'))},")
        add(f"      aliases: [{aliases}] }},")
    out[-1] = out[-1].rstrip(",")
    add("  ],")
    add("")

    # cities ----------------------------------------------------------------
    add("  cities: {")
    rows: list[tuple[str, float, float]] = []
    for tier in loc.get("tiers", []):
        for c in tier.get("cities", []):
            rows.append((c["name"].lower(), float(tier["score"]),
                         float(c.get("col_index", 100))))
    for c in loc.get("penalized", []):
        rows.append((c["name"].lower(), float(c.get("score", 0.3)),
                     float(c.get("col_index", 100))))
    pad = max(len(f"'{n}':") for n, _, _ in rows) + 1
    for name, score, col in rows:
        key = f"'{name}':".ljust(pad)
        add(f"    {key} {{ score: {score:.2f}, col: {col:g} }},")
    out[-1] = out[-1].rstrip(",")
    add("  },")
    add(f"  unlistedCity: {float(loc.get('unlisted_score', 0.45)):.2f},")
    add(f"  remoteScore: {float(loc.get('remote_score', 0.95)):.2f},")
    add("")

    # compensation ----------------------------------------------------------
    add(f"  comp: {{ floor: {int(comp['floor'])}, target: {int(comp['target'])}, "
        f"stretch: {int(comp.get('stretch', comp['target'] * 1.3))}, "
        f"floorScore: {float(comp.get('floor_score', 0.40)):.2f}, "
        f"targetScore: {float(comp.get('target_score', 0.85)):.2f}, "
        f"unknown: {float(comp.get('unknown_score', 0.55)):.2f} }},")
    add("")

    # industries ------------------------------------------------------------
    add("  industries: {")
    for name, words in ind.get("preferred", {}).items():
        joined = ", ".join(js(str(w).lower()) for w in words)
        add(f"    {js(name.replace('_', ' '))}: [{joined}],")
    out[-1] = out[-1].rstrip(",")
    add("  },")
    add(f"  industryNeutral: {float(ind.get('neutral_score', 0.55)):.2f},")
    add("")

    # signals ---------------------------------------------------------------
    for key, label in (("green", "green"), ("red", "red")):
        pairs = [f"[{js(s['phrase'].lower())}, {int(s.get('weight', 1))}]"
                 for s in sig.get(key, [])]
        add(f"  {label}: [")
        add(wrap_list(pairs, 10))
        add("  ],")
    out[-1] = out[-1].rstrip(",") + ","
    add("")

    # hard filters ----------------------------------------------------------
    for js_name, yaml_name in (("dropTitle", "drop_if_title_contains"),
                               ("dropDesc", "drop_if_description_contains"),
                               ("staffing", "staffing_agency_markers")):
        items = [js(str(t).lower()) for t in hf.get(yaml_name, [])]
        add(f"  {js_name}: [")
        add(wrap_list(items, 12))
        add("  ],")
    out[-1] = out[-1].rstrip(",")

    add("};")
    return "\n".join(out)


# ---------------------------------------------------------------------------

def splice(html: str, generated: str) -> str:
    start = html.index(BEGIN)
    header_end = html.index("*/", start) + 2
    end = html.index(END, header_end)
    return html[:header_end] + "\n" + generated + "\n\n" + html[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("yaml_path", nargs="?", default=str(DEFAULT_YAML),
                    help="path to Pathfinder's profile.yaml")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if index.html is out of date")
    args = ap.parse_args()

    yaml_path = Path(args.yaml_path).expanduser().resolve()
    if not yaml_path.exists():
        print(f"Could not find {yaml_path}.", file=sys.stderr)
        print("Pass the path explicitly: python3 build_profile.py "
              "../ProjectPathfinder/profile.yaml", file=sys.stderr)
        return 2

    profile = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    total = sum(profile["weights"].values())
    if round(total) != 100:
        print(f"Refusing to build: weights sum to {total}, not 100. "
              f"Fix profile.yaml first.", file=sys.stderr)
        return 2

    html = INDEX.read_text(encoding="utf-8")
    updated = splice(html, build(profile))

    if args.check:
        if updated != html:
            print("index.html is out of date. Run: python3 build_profile.py")
            return 1
        print("index.html is up to date.")
        return 0

    if updated == html:
        print("Already up to date, nothing written.")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    cities = sum(len(t["cities"]) for t in profile["location"]["tiers"]) \
        + len(profile["location"].get("penalized", []))
    aliases = sum(len(s.get("aliases", [])) for s in profile["skills"])
    print(f"Wrote {INDEX.name} from {yaml_path.name}: "
          f"{len(profile['role_families'])} role families, "
          f"{len(profile['skills'])} skills ({aliases} aliases), "
          f"{cities} cities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
