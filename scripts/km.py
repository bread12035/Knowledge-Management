#!/usr/bin/env python3
"""Knowledge-Management helper: deterministic parts of the dreaming workflow.

Standard library only. Run from the repo root.

  status                 new / changed / unchanged / failed raw files
  mark <raw>...          mark raw files as ingested (current sha256)
  fail <raw> <reason>    record an ingest failure
  index                  rebuild wiki/_index.md from frontmatter
  lint                   check frontmatter, links, orphans, sizes, PRIMER, bloat
  due [--days N] [--oldest K]   pages due for review + least recently dreamed
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
NOTES = ROOT / "notes"
WIKI = ROOT / "wiki"
STATE = ROOT / "dream" / "state.json"
PRIMER = ROOT / "PRIMER.md"
INDEX = WIKI / "_index.md"

SOURCES = ("ai-new-tech", "system-design")
TYPES = {
    "topic": ("topics", "主題總覽 Topics"),
    "concept": ("concepts", "概念 Concepts"),
    "pattern": ("patterns", "設計模式 Patterns"),
    "decision": ("decisions", "設計決定 Decisions"),
    "bridge": ("bridges", "跨領域連結 Bridges"),
}
STATUSES = {"active", "conflict", "superseded", "moved"}
REQUIRED = (
    "id", "title", "type", "summary", "domains", "sources", "evidence",
    "related", "status", "created", "last_dreamed", "review_count", "next_review",
)
PAGE_LIMIT = 8 * 1024
PRIMER_LIMIT = 4096
BLOAT_LIMIT = 1.2
MAX_FAILURES = 3
LINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)\]\]")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def links(body: str) -> set[str]:
    """[[slug]] links outside code fences and inline code."""
    return set(LINK_RE.findall(CODE_RE.sub("", body)))


def today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Taipei")).date()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body). Values: str or list[str]."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta: dict = {}
    for line in text[4:end].splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key.strip()] = [v.strip() for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = val
    return meta, text[end + 5:]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"version": 1, "raw": {}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")


def raw_files() -> list[Path]:
    return sorted(p for s in SOURCES for p in (RAW / s).glob("*.md"))


def note_path(raw: Path) -> Path:
    return NOTES / raw.parent.name / f"{raw.stem}.note.md"


def wiki_pages() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md") if p != INDEX)


# ---------------------------------------------------------------- commands

def cmd_status(_: list[str]) -> int:
    state = load_state()["raw"]
    seen = set()
    groups: dict[str, list[str]] = {"new": [], "changed": [], "failed": [], "unchanged": []}
    for p in raw_files():
        key = rel(p)
        seen.add(key)
        entry = state.get(key)
        if entry and entry.get("failures", 0) >= MAX_FAILURES and entry.get("sha256_failed") == sha256(p):
            groups["failed"].append(f"{key}  ({entry.get('last_error', '')})")
        elif not entry or not entry.get("sha256"):
            groups["new"].append(key)
        elif entry["sha256"] != sha256(p):
            groups["changed"].append(key)
        else:
            groups["unchanged"].append(key)
    missing = sorted(k for k in state if k not in seen)
    for name, items in groups.items():
        print(f"{name}: {len(items)}")
        for i in items:
            print(f"  {i}")
    if missing:
        print(f"missing (in state, not on disk): {len(missing)}")
        for m in missing:
            print(f"  {m}")
    return 0


def cmd_mark(args: list[str]) -> int:
    if not args:
        print("usage: km.py mark <raw-path>...", file=sys.stderr)
        return 2
    state = load_state()
    rc = 0
    for a in args:
        p = ROOT / a
        if not p.exists():
            print(f"error: {a} not found", file=sys.stderr)
            rc = 1
            continue
        n = note_path(p)
        if not n.exists():
            print(f"error: note {rel(n)} missing; write it before marking", file=sys.stderr)
            rc = 1
            continue
        state["raw"][rel(p)] = {
            "sha256": sha256(p),
            "note": rel(n),
            "ingested_at": today().isoformat(),
            "failures": 0,
        }
        print(f"marked {rel(p)}")
    save_state(state)
    return rc


def cmd_fail(args: list[str]) -> int:
    if len(args) < 2:
        print("usage: km.py fail <raw-path> <reason>", file=sys.stderr)
        return 2
    state = load_state()
    p = ROOT / args[0]
    entry = state["raw"].setdefault(rel(p), {})
    entry["failures"] = entry.get("failures", 0) + 1
    entry["last_error"] = " ".join(args[1:])
    entry["last_failed_at"] = today().isoformat()
    if p.exists():
        entry["sha256_failed"] = sha256(p)
    save_state(state)
    print(f"{rel(p)}: failures={entry['failures']}")
    return 0


def cmd_index(_: list[str]) -> int:
    groups: dict[str, list[tuple[str, str, list[str]]]] = {t: [] for t in TYPES}
    archived: list[tuple[str, str]] = []
    for p in wiki_pages():
        meta, _ = parse(p)
        status = meta.get("status", "active")
        if status == "moved" or meta.get("type") not in TYPES:
            continue
        item = (meta.get("id", p.stem), meta.get("summary", ""), meta.get("domains", []))
        if status == "superseded":
            archived.append(item[:2])
        else:
            groups[meta["type"]].append(item)
    lines = [
        "# Wiki Index",
        "",
        f"自動產生（`python3 scripts/km.py index`），請勿手改。更新日期：{today().isoformat()}。",
        "標記：`AI` = ai-new-tech，`SD` = system-design。引用格式：`KM:<slug>`。",
        "",
    ]
    tag = {"ai-new-tech": "AI", "system-design": "SD"}
    for t, (_, label) in TYPES.items():
        items = sorted(groups[t])
        lines.append(f"## {label}")
        lines.append("")
        if not items:
            lines.append("（尚無）")
        for slug, summary, domains in items:
            d = "/".join(tag.get(x, x) for x in domains)
            lines.append(f"- [[{slug}]] `{d}` — {summary}")
        lines.append("")
    if archived:
        lines.append("## 已取代 Archive")
        lines.append("")
        for slug, summary in sorted(archived):
            lines.append(f"- [[{slug}]] — {summary}")
        lines.append("")
    INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {rel(INDEX)}: {sum(len(v) for v in groups.values())} pages, {len(archived)} archived")
    return 0


def cmd_lint(_: list[str]) -> int:
    errors: list[str] = []
    warns: list[str] = []
    pages: dict[str, tuple[Path, dict, str]] = {}
    for p in wiki_pages():
        meta, body = parse(p)
        r = rel(p)
        if not meta:
            errors.append(f"{r}: no frontmatter")
            continue
        missing = [k for k in REQUIRED if k not in meta]
        if meta.get("status") == "moved":
            missing = [k for k in ("id", "status", "moved_to") if k not in meta]
        if missing:
            errors.append(f"{r}: missing fields {missing}")
        slug = meta.get("id", "")
        if slug != p.stem:
            errors.append(f"{r}: id '{slug}' != filename")
        if slug in pages:
            errors.append(f"{r}: duplicate id '{slug}' (also {rel(pages[slug][0])})")
        pages[slug] = (p, meta, body)
        status = meta.get("status", "")
        if status and status not in STATUSES:
            errors.append(f"{r}: bad status '{status}'")
        t = meta.get("type")
        if status != "moved":
            if t not in TYPES:
                errors.append(f"{r}: bad type '{t}'")
            else:
                folder = p.parent.name
                if folder != TYPES[t][0] and not (folder == "archive" and status == "superseded"):
                    errors.append(f"{r}: type '{t}' should live in wiki/{TYPES[t][0]}/")
            if t == "bridge" and set(meta.get("domains", [])) != set(SOURCES):
                errors.append(f"{r}: bridge must have both domains")
            for s in meta.get("sources", []):
                if not (ROOT / s.split("#")[0]).exists():
                    errors.append(f"{r}: source not found: {s}")
            size = len(p.read_bytes())
            if size > PAGE_LIMIT:
                warns.append(f"{r}: {size} bytes > {PAGE_LIMIT}; consider splitting")
    inbound: dict[str, int] = {s: 0 for s in pages}
    for slug, (p, meta, body) in pages.items():
        targets = links(body) | set(meta.get("related", []))
        if meta.get("moved_to"):
            targets.add(meta["moved_to"])
        for t in targets:
            if t not in pages:
                errors.append(f"{rel(p)}: broken link [[{t}]]")
            elif t != slug:
                inbound[t] += 1
        for t in meta.get("related", []):
            if t in pages and t not in links(body):
                warns.append(f"{rel(p)}: related '{t}' not linked in body")
    for slug, n in inbound.items():
        meta = pages[slug][1]
        if n == 0 and meta.get("status") == "active" and meta.get("type") != "topic":
            warns.append(f"{rel(pages[slug][0])}: orphan (no inbound links)")
    for n in sorted(NOTES.rglob("*.note.md")):
        meta, _ = parse(n)
        if not meta.get("raw") or not (ROOT / meta["raw"]).exists():
            errors.append(f"{rel(n)}: raw '{meta.get('raw')}' not found")
    if PRIMER.exists():
        chars = len(PRIMER.read_text(encoding="utf-8"))
        if chars > PRIMER_LIMIT:
            errors.append(f"PRIMER.md: {chars} chars > {PRIMER_LIMIT}")
    raw_bytes = sum(len(p.read_bytes()) for p in raw_files())
    wiki_bytes = sum(len(p.read_bytes()) for p in wiki_pages())
    ratio = wiki_bytes / raw_bytes if raw_bytes else 0.0
    conflicts = [s for s, (_, m, _) in pages.items() if m.get("status") == "conflict"]
    print(f"pages: {len(pages)}  raw: {raw_bytes} B  wiki: {wiki_bytes} B  ratio: {ratio:.2f}")
    if ratio > BLOAT_LIMIT:
        warns.append(f"wiki/raw ratio {ratio:.2f} > {BLOAT_LIMIT}: compress in next dreaming run")
    if conflicts:
        print(f"conflict pages: {', '.join(sorted(conflicts))}")
    for e in errors:
        print(f"ERROR {e}")
    for w in warns:
        print(f"WARN  {w}")
    print(f"{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


def cmd_due(args: list[str]) -> int:
    days, oldest = 0, 8
    if "--days" in args:
        days = int(args[args.index("--days") + 1])
    if "--oldest" in args:
        oldest = int(args[args.index("--oldest") + 1])
    limit = today() + dt.timedelta(days=days)
    rows = []
    for p in wiki_pages():
        meta, _ = parse(p)
        if meta.get("status") in ("moved", "superseded"):
            continue
        rows.append((meta.get("next_review", "9999-12-31"), meta.get("last_dreamed", "0000-01-01"),
                     meta.get("id", p.stem), rel(p)))
    due = sorted(r for r in rows if r[0] <= limit.isoformat())
    print(f"due by {limit.isoformat()}: {len(due)}")
    for nr, _, slug, r in due:
        print(f"  {nr}  {slug}  {r}")
    stale = sorted(rows, key=lambda r: r[1])[:oldest]
    print(f"least recently dreamed (top {oldest}):")
    for _, ld, slug, r in stale:
        print(f"  {ld}  {slug}  {r}")
    return 0


COMMANDS = {
    "status": cmd_status, "mark": cmd_mark, "fail": cmd_fail,
    "index": cmd_index, "lint": cmd_lint, "due": cmd_due,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]))
