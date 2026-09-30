#!/usr/bin/env python3
"""Validate a write-spec document and optionally save it atomically.

Checks only mechanical rules: structure, table shapes, inventory consistency
between Section 4 and Section 9, counts, fences, and safe file placement.
It does not judge content.

Usage:
  validate_spec.py DRAFT.md                      # validate, print JSON
  validate_spec.py DRAFT.md --save design/x-spec.md [--replace]
Exit code 0 = valid (and saved, if requested); 1 = invalid; 2 = usage or save error.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HEADINGS = [
    "## 1. The requirement",
    "## 2. Grounding — reuse before building",
    "## 3. Architecture",
    "## 4. Metadata changes",
    "## 5. Data 360 (Data Cloud) data involved",
    "## 6. Security considerations",
    "## 7. Testing strategy",
    "## 8. Open decisions",
    "## 9. Change set",
]
DISCLAIMER = "Specification only — nothing is implemented or deployed."
REQ_HEADER = "| # | Responsibility | Trigger | Where it lives |"
CS_HEADER = "| # | Action | Type | API name | Module | Why |"
ACTIONS = ("Create", "Update", "Delete")
ZERO = "no metadata changes are required"
BULLET_RE = re.compile(r"^- \*\*(Create|Update|Delete) `([^`]+)`\*\* — (.+)$")
LOOSE_BULLET_RE = re.compile(r"^- \*\*(\w+) `")
COUNTS_RE = re.compile(r"^Total: (\d+) · Create: (\d+) · Update: (\d+) · Delete: (\d+)$", re.M)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-spec\.md$")
SEP_RE = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+$")
BANNED = ("hero", "seam", "moving parts")


def split_cells(row):
    """Split a Markdown table row on unescaped pipes."""
    body = row.strip()
    if not (body.startswith("|") and body.endswith("|")) or body.endswith("\\|"):
        return None
    cells = re.split(r"(?<!\\)\|", body[1:-1])
    return [c.strip() for c in cells]


def table_after(lines, header):
    """Return (found, rows) for the table that starts with header."""
    for i, line in enumerate(lines):
        if line.strip() == header:
            rows = []
            if i + 1 >= len(lines) or not SEP_RE.match(lines[i + 1].strip()):
                return True, None
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append(row)
            return True, rows
    return False, []


def sections(text):
    """Map heading -> body lines, outside code fences."""
    out, cur, fence = {}, None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            cur = line.strip()
            out.setdefault(cur, [])
            out[cur + "#count"] = out.get(cur + "#count", 0) + 1
            continue
        if cur:
            out[cur].append(line)
    return out


def validate(text, filename=""):
    errors, warnings = [], []
    lines = text.splitlines()

    # Preamble
    first = next((l for l in lines if l.strip()), "")
    draft = "-draft-" in filename or filename.endswith("-draft-spec.md")
    if not first.startswith("# Implementation spec — "):
        errors.append("first line must be '# Implementation spec — {title}'")
    elif draft != ("Draft" in first):
        errors.append("Draft title and '-draft-spec.md' filename must be used together")
    if not any(l.startswith("> ") for l in lines[:6]):
        errors.append("missing one-line purpose blockquote after the title")
    if DISCLAIMER not in text:
        errors.append(f"missing disclaimer text: {DISCLAIMER!r}")

    # Code fences
    fences = [l for l in lines if l.startswith("```")]
    if len(fences) % 2:
        errors.append("unbalanced code fences")

    # Headings: exact, ordered, once each, nothing else at level 2
    sec = sections(text)
    in_fence = False
    found = []
    for l in lines:
        if l.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and l.startswith("## "):
            found.append(l.strip())
    if found != HEADINGS:
        missing = [h for h in HEADINGS if h not in found]
        extra = [h for h in found if h not in HEADINGS]
        dup = [h for h, n in Counter(found).items() if n > 1]
        errors.append(f"level-2 headings must be exactly the nine required headings in order "
                      f"(missing={missing}, unexpected={extra}, duplicated={dup})")
    for h in HEADINGS:
        body = [l for l in sec.get(h, []) if l.strip() and l.strip() != "---"]
        if h in sec and not body:
            errors.append(f"section is empty: {h}")

    # Section 1 table
    s1 = sec.get(HEADINGS[0], [])
    ok, rows = table_after(s1, REQ_HEADER)
    if not ok:
        errors.append("Section 1 must contain the table header " + REQ_HEADER)
    elif rows is None:
        errors.append("Section 1 table is missing its separator row")
    elif not rows:
        errors.append("Section 1 table has no rows")
    else:
        for r in rows:
            c = split_cells(r)
            if c is None or len(c) != 4:
                errors.append(f"Section 1 row must have 4 cells: {r.strip()[:80]}")

    # Section 4 bullets
    s4 = sec.get(HEADINGS[3], [])
    s4_items = []
    for l in s4:
        m = BULLET_RE.match(l.strip())
        if m:
            s4_items.append((m.group(1), m.group(2)))
        elif LOOSE_BULLET_RE.match(l.strip()):
            errors.append(f"Section 4 change bullet has the wrong format: {l.strip()[:80]}")
    s4_zero = ZERO in " ".join(s4).lower()

    # Section 9 table
    s9 = sec.get(HEADINGS[8], [])
    ok, rows = table_after(s9, CS_HEADER)
    s9_items, s9_types = [], []
    if not ok:
        errors.append("Section 9 must contain the table header " + CS_HEADER)
        rows = []
    elif rows is None:
        errors.append("Section 9 table is missing its separator row")
        rows = []
    for n, r in enumerate(rows, 1):
        c = split_cells(r)
        if c is None or len(c) != 6:
            errors.append(f"Section 9 row must have 6 cells (escape '|' as '\\|'): {r.strip()[:80]}")
            continue
        num, action, typ, api, module, why = c
        if num != str(n):
            errors.append(f"Section 9 rows must be numbered 1..N in order; row {n} has {num!r}")
        if action not in ACTIONS:
            errors.append(f"Section 9 row {n}: action must be Create, Update, or Delete, got {action!r}")
        m = re.fullmatch(r"`([^`]+)`", api)
        if not m:
            errors.append(f"Section 9 row {n}: API name must be in backticks, got {api!r}")
            continue
        for label, val in (("Type", typ), ("Module", module), ("Why", why)):
            if not val:
                errors.append(f"Section 9 row {n}: {label} is empty")
        s9_items.append((action, m.group(1)))
        s9_types.append((typ, m.group(1)))
    s9_zero = ZERO in " ".join(s9).lower()

    # Inventory consistency
    # Identity is (Type, API name): an object and its tab may share a name.
    dup = [k for k, n in Counter(s9_types).items() if n > 1]
    if dup:
        errors.append(f"Section 9 lists the same (Type, API name) more than once: {dup}")
    if Counter(s4_items) != Counter(s9_items):
        only4 = sorted(set(s4_items) - set(s9_items))
        only9 = sorted(set(s9_items) - set(s4_items))
        errors.append(f"Sections 4 and 9 must list the same changes (only in 4: {only4}; only in 9: {only9})")
    if not s9_items:
        if not (s4_zero and s9_zero):
            errors.append("a zero-change spec must state 'No metadata changes are required' in Sections 4 and 9")
    elif s4_zero or s9_zero:
        errors.append("spec lists changes but also states that no metadata changes are required")

    # Counts
    c = Counter(a for a, _ in s9_items)
    expect = (len(s9_items), c["Create"], c["Update"], c["Delete"])
    m = COUNTS_RE.findall("\n".join(s9))
    if len(m) != 1:
        errors.append("Section 9 must contain exactly one line 'Total: N · Create: N · Update: N · Delete: N'")
    elif tuple(int(x) for x in m[0]) != expect:
        errors.append(f"counts line {m[0]} does not match the table {expect}")

    # Conditional changes must appear in Section 8
    s8 = "\n".join(sec.get(HEADINGS[7], []))
    for r in rows:
        cells = split_cells(r) or []
        if len(cells) == 6 and "conditional:" in cells[5].lower():
            api = cells[3].strip("`")
            if api not in s8:
                errors.append(f"conditional change `{api}` must be listed in Section 8 with its condition")

    # Evidence provenance in Section 2
    s2 = " ".join(sec.get(HEADINGS[1], [])).lower()
    if "reported by askcoworker" not in s2 and "verified by org query" not in s2:
        errors.append("Section 2 must mark facts as 'reported by AskCoworker' or 'verified by org query'")

    # Mermaid: quoted labels
    in_m = False
    for l in lines:
        if l.strip().startswith("```mermaid"):
            in_m = True
            continue
        if in_m and l.startswith("```"):
            in_m = False
            continue
        if in_m:
            bare = re.sub(r'"[^"]*"', '""', l)  # blank out quoted text
            if re.search(r'\w(?:\[\[|\[\(|\(\(|\{\{|\[|\(|\{)(?!")', bare):
                errors.append(f"Mermaid node label must be quoted: {l.strip()[:80]}")
            if any(lab != '""' for lab in re.findall(r"\|([^|]*)\|", bare)):
                errors.append(f"Mermaid edge label must be quoted: {l.strip()[:80]}")

    low = text.lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}s?\b", low):
            warnings.append(f"avoid the metaphor {w!r}")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "counts": dict(zip(("total", "create", "update", "delete"), expect))}


def safe_save(src, target, replace, root):
    """Atomically move src to target inside root/design (or a directory the user chose inside root)."""
    root = Path(root).resolve()
    t = Path(target)
    if t.is_absolute() or ".." in t.parts:
        raise ValueError("target must be a relative path without '..'")
    if not NAME_RE.match(t.name) and not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*-draft-spec\.md$", t.name):
        raise ValueError("file name must be lowercase-hyphenated and end with -spec.md")
    dest_dir = (root / t.parent)
    if dest_dir.is_symlink() or (root / t).is_symlink():
        raise ValueError("refusing to write through a symlink")
    dest_dir.mkdir(parents=True, exist_ok=True)
    real = (dest_dir.resolve() / t.name)
    if root not in real.parents:
        raise ValueError("target resolves outside the project")
    if real.exists() and not replace:
        raise FileExistsError(f"{t} exists; pass --replace only if it is the same specification")
    tmp = real.with_name(f".{t.name}.tmp")
    tmp.write_text(Path(src).read_text())
    os.replace(tmp, real)
    return str(real)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--save", help="relative target path, e.g. design/foo-spec.md")
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    try:
        text = Path(a.file).read_text()
    except OSError as e:
        print(json.dumps({"ok": False, "errors": [str(e)]}))
        return 2
    res = validate(text, Path(a.save or a.file).name)
    if res["ok"] and a.save:
        try:
            res["saved"] = safe_save(a.file, a.save, a.replace, a.root)
        except (ValueError, OSError) as e:
            res["ok"] = False
            res["errors"].append(f"save failed: {e}")
            print(json.dumps(res, indent=1))
            return 2
    print(json.dumps(res, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
