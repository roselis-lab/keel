"""One search across everything Keel holds.

Splitting search by entity type pushes a question onto the caller that they cannot
answer yet. Someone asking "does Keel have anything about tool misuse?" does not know
whether the answer is a threat, a control, a row of the coverage matrix, or a system
that already ran into it — that is what they are asking. Making them guess costs three
calls and a wrong assumption.

So one query runs over all four, and every hit says which kind it is and what matched.
Hits are deliberately thin: an id, a title, and the field the query was found in. A
search result is a decision about what to fetch next, not the fetch itself.
"""
from __future__ import annotations

from typing import Any

from keel.services import coverage_service, report_service
from keel.store import get_store

KINDS = ("threat", "mitigation", "coverage", "report")


def _hit(kind: str, ident: str, title: str, field: str, text: str, q: str,
         rank: int = 1) -> dict[str, Any]:
    """A hit carries the snippet around the match, so a caller can tell a real hit from a
    coincidence without a second call. `rank` orders name matches above prose matches;
    it is stripped before the result goes out."""
    low = text.lower()
    at = low.find(q)
    start, end = max(0, at - 40), min(len(text), at + len(q) + 60)
    snippet = ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")
    return {"_rank": rank, "kind": kind, "id": ident, "title": title,
            "matched_in": field, "snippet": snippet}


def _text_of(value: Any) -> str:
    """Flatten a field to searchable text. Lists of dicts (weaknesses, references, faq)
    carry most of the prose in this catalog, so skipping them would miss the good part."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_text_of(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_text_of(v) for v in value)
    return str(value)


def _scan(record: dict[str, Any], q: str, skip: tuple[str, ...]) -> tuple[str, str] | None:
    """First field whose text contains the query, and that text."""
    for key, value in record.items():
        if key in skip:
            continue
        text = _text_of(value)
        if q in text.lower():
            return key, text
    return None


def search(q: str, kind: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Case-insensitive substring search. Returns {hits, count, truncated}."""
    q = (q or "").strip().lower()
    if len(q) < 2:
        return {"hits": [], "count": 0, "truncated": False,
                "error": "a query needs at least two characters"}
    if kind and kind not in KINDS:
        return {"hits": [], "count": 0, "truncated": False,
                "error": f"unknown kind {kind!r}. Use one of: {', '.join(KINDS)}"}

    store = get_store()
    hits: list[dict[str, Any]] = []

    if kind in (None, "threat"):
        for tid, rec in store.threats.items():
            title = rec.get("title") or tid
            if q in tid.lower() or q in title.lower():
                hits.append(_hit("threat", tid, title, "title", f"{tid} {title}", q, rank=0))
                continue
            # `mitigations` is skipped: a match there means the CONTROL matched, and the
            # control comes back as its own hit. Including the threat too puts the weaker
            # signal in front of the stronger one.
            found = _scan(rec, q, skip=("id", "title", "mitigations"))
            if found:
                hits.append(_hit("threat", tid, title, found[0], found[1], q))

    if kind in (None, "mitigation"):
        for mid, rec in store.mitigations.items():
            name = rec.get("name") or mid
            if q in mid.lower() or q in name.lower():
                hits.append(_hit("mitigation", mid, name, "name", f"{mid} {name}", q, rank=0))
                continue
            found = _scan(rec, q, skip=("id", "name"))
            if found:
                hits.append(_hit("mitigation", mid, name, found[0], found[1], q))

    if kind in (None, "coverage"):
        for doc in coverage_service.load_sources():
            for entry in doc.entries:
                blob = " ".join(filter(None, [entry.ref, entry.title, entry.group, entry.note]))
                if q in blob.lower():
                    rank = 0 if q in f"{entry.ref} {entry.title}".lower() else 1
                    hit = _hit("coverage", f"{doc.source.id}:{entry.ref}", entry.title,
                               "entry", blob, q, rank=rank)
                    hit["state"] = entry.state
                    hits.append(hit)

    if kind in (None, "report"):
        for row in report_service.list_reports():
            blob = " ".join(filter(None, [row["system_id"], row["system_name"],
                                          row.get("keywords") or ""]))
            if q in blob.lower():
                rank = 0 if q in f'{row["system_id"]} {row["system_name"]}'.lower() else 1
                hit = _hit("report", row["system_id"], row["system_name"], "assessment",
                           blob, q, rank=rank)
                hit["latest_date"] = row["latest_date"]
                hits.append(hit)

    # Named matches first — a card called "Code sandbox" is a better answer to "sandbox"
    # than one that mentions the word halfway through its failure behaviour.
    hits.sort(key=lambda h: (h["_rank"], h["kind"], h["id"]))
    total = len(hits)
    out = [{k: v for k, v in h.items() if k != "_rank"} for h in hits[:limit]]
    return {"hits": out, "count": total, "truncated": total > limit}
