"""
dossier_analyze.py -- deterministic analysis of a constituted dossier (no LLM).

Given a dossier's saved sources, it:
  * extracts the dated passages mentioning the subject / selectors -- the
    "before/now" juxtaposition the analyst reads to judge coherence, and
  * runs the open-extraction engine over all source texts for entities.

Indice surfaces and aligns; the human judges.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_SENT = re.compile(r"[^.!?\n]+[.!?]?")


def _selectors(dossier: Dict[str, Any], extra: str) -> List[str]:
    raw = (dossier.get("name", "") or "") + " " + (extra or "")
    out, seen = [], set()
    for t in re.split(r"[,\s]+", raw):
        t = t.strip()
        if len(t) >= 3 and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def _passages_for(text: str, selectors: List[str]) -> List[Dict[str, Any]]:
    out = []
    for m in _SENT.finditer(text or ""):
        s = m.group().strip()
        if not s:
            continue
        low = s.lower()
        hit = sorted({sel for sel in selectors if sel.lower() in low})
        if hit:
            out.append({"passage": s[:400], "matched": hit})
    return out


def _date_key(d: str) -> str:
    return (d or "").strip() or "9999"  # empty dates sort last


def analyze(dossier: Dict[str, Any], extra_selectors: str = "") -> Dict[str, Any]:
    selectors = _selectors(dossier, extra_selectors)
    sources = dossier.get("sources", [])

    # 1) dated juxtaposition passages (oldest first = "avant" -> "maintenant")
    passages: List[Dict[str, Any]] = []
    for src in sources:
        for p in _passages_for(src.get("raw_text", ""), selectors):
            passages.append({
                "date": src.get("published_date", ""),
                "title": src.get("title", ""),
                "url": src.get("url", ""),
                "platform": src.get("platform", ""),
                "orientation": src.get("orientation", "unknown"),
                "passage": p["passage"],
                "matched": p["matched"],
            })
    passages.sort(key=lambda x: _date_key(x["date"]))

    # 2) entities via the open-extraction engine (deterministic, no spaCy)
    entities: List[Dict[str, Any]] = []
    try:
        from .indice_core import CorrelationEngine
        from . import packs
        try:
            profile = packs.load_domains(["justice"])
        except Exception:
            profile = {"patterns": [], "lexicon": []}
        engine = CorrelationEngine(profile, watchlist=selectors, use_ner=False)
        for src in sources:
            for line in (src.get("raw_text", "") or "").splitlines():
                line = line.strip()
                if line:
                    engine.analyze_utterance(line)
        entities = [{"name": k, "category": v.get("category"), "count": v.get("count")}
                    for k, v in engine.entities.items()]
        entities.sort(key=lambda e: -(e.get("count") or 0))
        entities = entities[:40]
    except Exception:
        entities = []

    return {"selectors": selectors, "sources": len(sources),
            "passages": passages, "entities": entities}


def build_graph(dossier: Dict[str, Any], extra_selectors: str = "") -> Dict[str, Any]:
    # Deterministic {nodes, edges, events} for the interactive view (graph / timeline / files).
    # Reuses analyze() for entities + selectors; co-occurrence is computed from shared sources.
    import itertools
    res = analyze(dossier, extra_selectors)
    selectors = res.get("selectors", [])
    ents = res.get("entities", [])
    sel_low = {s.lower() for s in selectors}
    sources = dossier.get("sources", [])

    low = [(e["name"], (e["name"] or "").lower(), e) for e in ents]
    ent_sources: Dict[str, List[str]] = {e["name"]: [] for e in ents}
    src_entities: Dict[str, List[str]] = {}
    nodes: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    for src in sources:
        sid = src.get("id") or ""
        text = (src.get("raw_text") or "").lower()
        present = [name for (name, nlow, _e) in low if nlow and nlow in text]
        src_entities[sid] = present
        for name in present:
            ent_sources[name].append(sid)
        nodes.append({
            "id": "s:" + sid, "kind": "source",
            "label": src.get("title") or src.get("url") or sid,
            "category": src.get("type") or "doc",
            "date": src.get("published_date") or "",
            "orientation": src.get("orientation") or "unknown",
            "url": src.get("url") or "",
            "excerpt": (src.get("raw_text") or "").strip()[:220],
            "entities": present,
        })
        if src.get("published_date"):
            events.append({
                "id": "ev:" + sid, "date": src.get("published_date") or "",
                "label": src.get("title") or sid, "category": src.get("type") or "doc",
                "source_id": sid, "url": src.get("url") or "",
                "orientation": src.get("orientation") or "unknown",
            })

    edges: List[Dict[str, Any]] = []
    eid = 0
    for e in ents:
        nm = e["name"]
        nodes.append({
            "id": "e:" + nm, "kind": "entity", "label": nm,
            "category": e.get("category") or "ENTITY",
            "count": e.get("count") or 0,
            "sources": ent_sources.get(nm, []),
            "is_selector": (nm or "").lower() in sel_low,
        })
        for sid in ent_sources.get(nm, []):
            edges.append({"id": "m%d" % eid, "source": "e:" + nm, "target": "s:" + sid,
                          "kind": "mention", "weight": 1})
            eid += 1

    pair_count: Dict[Any, int] = {}
    pair_src: Dict[Any, List[str]] = {}
    for sid, names in src_entities.items():
        for a, b in itertools.combinations(sorted(set(names)), 2):
            pair_count[(a, b)] = pair_count.get((a, b), 0) + 1
            pair_src.setdefault((a, b), []).append(sid)
    for (a, b), w in sorted(pair_count.items(), key=lambda kv: (-kv[1], kv[0])):
        edges.append({"id": "c%d" % eid, "source": "e:" + a, "target": "e:" + b,
                      "kind": "cooccur", "weight": w, "provenance": pair_src[(a, b)]})
        eid += 1

    events.sort(key=lambda x: (x.get("date") or "9999"))
    return {
        "dossier_id": dossier.get("id"),
        "name": dossier.get("name"),
        "selectors": selectors,
        "counts": {"entities": len(ents), "sources": len(sources),
                   "cooccur_edges": len(pair_count), "events": len(events)},
        "nodes": nodes, "edges": edges, "events": events,
    }
