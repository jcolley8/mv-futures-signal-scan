#!/usr/bin/env python3
"""
MV Futures Signal Scan — corpus assembler.

Usage:  python3 assemble.py <dir-of-drive-files> signals.json

Rebuilds the full cumulative corpus from:
  base-signals.json        the accumulated corpus up to the base date
  delta-YYYY-MM-DD.json    one small file per daily scan

Each daily scan only ever has to write its own small delta, so the upload
size stays roughly constant instead of growing with the corpus. History is
reconstructed here, deterministically, at build time.

A delta may contain any of:
  new_signals              [ {signal objects} ]
  sightings                { "<signal id>": <int new count> }
  critical_uncertainties   [ {…} ]   replaces the current set
  scenario                 {…}       prepended to the scenario archive
  challenger               {…}       strongest uncertainty NOT on the list
  sectors                  [ "…" ]   replaces the sector list
  archived                 [ "<signal id>" ]  marks entries archived
"""
import json, sys, os, glob, re

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "drive"
OUT = sys.argv[2] if len(sys.argv) > 2 else "signals.json"

base_path = os.path.join(SRC_DIR, "base-signals.json")
if not os.path.exists(base_path):
    sys.exit(f"FATAL: {base_path} missing — cannot assemble without the base corpus.")

corpus = json.load(open(base_path))
corpus.setdefault("signals", [])
corpus.setdefault("critical_uncertainties", [])
corpus.setdefault("scenarios", [])
by_id = {s["id"]: s for s in corpus["signals"]}

deltas = []
for p in glob.glob(os.path.join(SRC_DIR, "delta-*.json")):
    m = re.search(r"delta-(\d{4}-\d{2}-\d{2})\.json$", os.path.basename(p))
    if m:
        deltas.append((m.group(1), p))
deltas.sort()

print(f"base: {len(corpus['signals'])} signals, scan_count {corpus.get('scan_count')}")
if not deltas:
    print("no deltas found — publishing the base corpus unchanged")

applied = 0
for date, path in deltas:
    try:
        d = json.load(open(path))
    except Exception as e:
        print(f"  !! {os.path.basename(path)} unreadable ({e}) — SKIPPED")
        continue

    added = skipped = bumped = 0
    for s in d.get("new_signals", []):
        sid = s.get("id")
        if not sid or sid in by_id:
            skipped += 1
            continue
        s.setdefault("first_seen", date)
        s.setdefault("sightings", 1)
        by_id[sid] = s
        corpus["signals"].append(s)
        added += 1

    for sid, n in (d.get("sightings") or {}).items():
        if sid in by_id:
            try:
                by_id[sid]["sightings"] = max(int(by_id[sid].get("sightings", 1)), int(n))
                bumped += 1
            except (TypeError, ValueError):
                pass

    for sid in d.get("archived", []):
        if sid in by_id:
            by_id[sid]["archived"] = True

    if d.get("critical_uncertainties"):
        corpus["critical_uncertainties"] = d["critical_uncertainties"]
    if d.get("sectors"):
        corpus["sectors"] = d["sectors"]
    if d.get("challenger"):
        ch = d["challenger"]
        prev = corpus.get("challenger") or {}
        # preserve the date this challenger first started knocking
        if prev.get("id") and prev.get("id") == ch.get("id"):
            ch.setdefault("first_noted", prev.get("first_noted", date))
        else:
            ch.setdefault("first_noted", date)
        corpus["challenger"] = ch
    if d.get("scenario"):
        sc = d["scenario"]
        corpus["scenarios"] = ([sc] + [x for x in corpus["scenarios"]
                                       if x.get("id") != sc.get("id")])

    corpus["last_updated"] = date
    corpus["scan_count"] = int(corpus.get("scan_count", 0)) + 1
    applied += 1
    print(f"  + {date}: {added} new, {skipped} dup, {bumped} sightings bumped, "
          f"CUs {'replaced' if d.get('critical_uncertainties') else 'unchanged'}, "
          f"scenario {'yes' if d.get('scenario') else 'no'}")

# guard against a delta that silently emptied things out
if not corpus["signals"]:
    sys.exit("FATAL: assembled corpus has zero signals — refusing to publish.")

json.dump(corpus, open(OUT, "w"), indent=1, ensure_ascii=False)
print(f"assembled {len(corpus['signals'])} signals from base + {applied} delta(s) "
      f"→ {OUT} ({os.path.getsize(OUT)} bytes), last_updated {corpus.get('last_updated')}")
