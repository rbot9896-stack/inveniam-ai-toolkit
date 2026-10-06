#!/usr/bin/env python3
"""Pull ANY deal from the Inveniam API: deal record, folders, documents, every
extracted field (flattened to cells.json / cells.csv) and on-chain anchoring
records per document. Cross-platform, standard library only.

    cd ~/dev/inveniam
    python3 tools/fetch_deal.py --env sales "The Meridian"      # by title (case-insensitive substring)
    python3 tools/fetch_deal.py --env sales 26ca3be5-ac61-...   # or by deal id
    python3 tools/fetch_deal.py "Inveniam Capital"              # production (default env)
    (INV_ENV=sales also works instead of --env; on Windows use `python`)

Options:
    --no-anchoring   skip the per-document anchoring (taxonomy) calls
    --refresh        ignore cached per-document results from an earlier run

Output goes to deals/<slug>/ next to inv.py. Per-document results are cached in
deals/<slug>/art/ and tax/, so a run that stops part-way (network drop, laptop
sleep) picks up where it left off. Calls are sequential on purpose: parallel
calls produce empty responses. Exit status 3 means the pull is incomplete (the
summary line says what is missing); rerun to fill the gaps.
"""
import csv, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import inv  # noqa: E402

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
ART_PAGE = 50   # the deal-level artifact list fails (HTTP 500) at larger pages on big deals


def fetch(path, env, tries=3, wait=4):
    """GET with retries. Returns parsed JSON, or None on 404 / persistent failure."""
    for attempt in range(1, tries + 1):
        try:
            status, body = inv.call("GET", path, env)
        except Exception as e:                       # network error, timeout
            status, body = 0, str(e).encode()
        if status == 404:
            return None
        if status // 100 == 2 and body.strip():
            try:
                return json.loads(body)
            except ValueError:
                pass
        if attempt < tries:
            time.sleep(wait)
    return None


def paged(path, env, limit=100, key="id"):
    """All items of a {items, meta} list, de-duplicated (page order is not stable)."""
    seen, page = {}, 1
    sep = "&" if "?" in path else "?"
    while True:
        d = fetch(f"{path}{sep}page={page}&limit={limit}", env)
        if d is None:
            return None if page == 1 else list(seen.values())
        items = d.get("items", [])
        for it in items:
            seen[it.get(key) if key else len(seen)] = it
        total_pages = (d.get("meta") or {}).get("totalPages")
        if not items or len(items) < limit or (total_pages and page >= total_pages):
            return list(seen.values())
        page += 1


class Progress:
    """One line per update: done/total, rate, ETA. No animation."""
    def __init__(self, label, total):
        self.label, self.total, self.t0, self.last = label, total, time.time(), 0
    def tick(self, done, note=""):
        now = time.time()
        if done < self.total and now - self.last < 5:
            return
        self.last = now
        el = now - self.t0
        eta = (el / done) * (self.total - done) if done else 0
        print(f"  {self.label}: {done}/{self.total}  {el:5.0f}s elapsed  ETA {eta:4.0f}s  {note}", flush=True)


def cache(out, did, art):
    with open(os.path.join(out, "art", did + ".json"), "w", encoding="utf-8") as fh:
        json.dump(art, fh)


def flatten(art, deal_id):
    """One artifact -> rows {doc, docId, ctype, form, rec, field, value, page, box, bb, url, built}."""
    s = art["sourceAttributes"]
    rows = []
    for fo in art["extractedData"]["forms"]:
        meta = {m["fieldId"]: m["fieldName"] for m in fo["records"].get("extractedFieldMetaData", [])}
        for rec in fo["records"].get("extractedFieldData", []):
            for fd in rec["fieldData"]:
                locs = fd.get("fieldLocations") or []
                bb = [[l.get("Page")] + [((l.get("Geometry") or {}).get("BoundingBox") or {}).get(k)
                                          for k in ("Left", "Top", "Width", "Height")] for l in locs]
                rows.append(dict(
                    doc=s["documentName"], docId=s["documentid"], ctype=s.get("contentType"),
                    form=fo["formName"], rec=rec["recordSequence"],
                    field=meta.get(fd["fieldId"], fd.get("fieldQueryName")), value=fd.get("value"),
                    page=locs[0].get("Page") if locs else None,
                    # some locations carry blank-string coordinates: only numbers count as a highlight
                    box=bool(bb) and all(isinstance(v, (int, float)) for v in bb[0][1:]),
                    bb=bb, url=(fd.get("sourceAttributes") or {}).get("fieldPreviewURL"), built=False,
                    _ids=(fo.get("formId"), rec.get("recordId"), fd["fieldId"])))
    # Values set by hand in an automatically extracted record come back without a preview link.
    # Build one from the ids, in the platform's own format (viewer host and prev= taken from a sibling link).
    sib = next((r["url"] for r in rows if r["url"] and "prev=" in r["url"]), None)
    for r in rows:
        f, rc, x = r.pop("_ids")
        if not r["url"] and sib and r["value"] not in (None, "") and r["page"] and f and rc:
            base, prev = sib.split("/view-file/")[0], sib.split("prev=")[1].split("&")[0]
            r["url"] = f"{base}/view-file/{r['docId']}?id={deal_id}&prev={prev}&formId={f}&recordId={rc}&fieldId={x}"
            r["built"] = True
    return rows


def main(argv):
    env = os.environ.get("INV_ENV", "prod")
    a = list(argv)
    anchoring = "--no-anchoring" not in a
    refresh = "--refresh" in a
    a = [x for x in a if x not in ("--no-anchoring", "--refresh")]
    if a[:1] == ["--env"]:
        env = a[1]; a = a[2:]
    if not a:
        sys.exit(__doc__)
    q = a[0]

    if UUID.match(q):
        deal = fetch(f"/v2/deals/{q}", env)
        if not deal:
            sys.exit(f"deal {q} not found in {env}")
    else:
        items = paged("/v2/deals", env) or []
        m = [i for i in items if q.lower() in (i.get("title") or "").lower()]
        if not m:
            sys.exit(f"no deal title contains: {q} ({len(items)} deals in {env})")
        exact = [i for i in m if (i.get("title") or "").lower() == q.lower()]
        if len(m) > 1 and len(exact) != 1:
            sys.exit("ambiguous, matches: " + "; ".join(i["title"] for i in m))
        deal = fetch(f"/v2/deals/{(exact or m)[0]['id']}", env)
    d, title = deal["id"], deal["title"]

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    out = os.path.join(ROOT, "deals", slug)
    for sub in ("art", "tax"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    print(f"deal: {title} ({d}) env: {env} -> {out}", flush=True)

    def save(name, obj):
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    save("deal.json", deal)
    folders = paged(f"/v2/dataroom/deals/{d}/folders", env)
    docs = paged(f"/v2/dataroom/deals/{d}/documents", env)
    if folders is None or docs is None:
        sys.exit("could not list folders/documents (a new deal has no data room until a storage provider is connected)")
    save("folders.json", {"items": folders})
    save("docs.json", {"items": docs})
    print(f"  {len(docs)} documents in {len(folders)} folders", flush=True)

    # Extracted data. The deal-level list is one call per 50 documents but can fail or skip/duplicate
    # across pages on big deals; whatever it misses is fetched per document and cached in art/.
    arts = {}
    if not refresh:
        for x in docs:
            p = os.path.join(out, "art", x["id"] + ".json")
            if os.path.exists(p) and os.path.getsize(p):
                arts[x["id"]] = json.load(open(p, encoding="utf-8"))
    missing = [x for x in docs if x["id"] not in arts]
    if missing:
        print(f"artifacts: deal-level list (pages of {ART_PAGE}) ..", flush=True)
        listed = paged(f"/v2/dataroom/datalab-provider/{d}/artifacts", env, limit=ART_PAGE, key=None) or []
        for it in listed:
            did = (it.get("sourceAttributes") or {}).get("documentid")
            if did and it.get("extractedData") and did not in arts:
                arts[did] = it
                cache(out, did, it)
        print(f"  list returned {len(listed)} records, {len(arts)} distinct documents", flush=True)
    missing = [x for x in docs if x["id"] not in arts]
    none_found = set()
    if missing:
        print(f"artifacts: {len(missing)} documents not in the list, fetching one by one (some simply have no extraction) ..", flush=True)
        pr = Progress("per-document artifacts", len(missing))
        for i, x in enumerate(missing, 1):
            one = fetch(f"/v2/dataroom/datalab-provider/{d}/artifacts/{x['id']}", env, tries=2)
            if isinstance(one, dict) and "extractedData" not in one:
                one = (one.get("items") or [None])[0]
            if one and one.get("extractedData"):
                arts[x["id"]] = one
                cache(out, x["id"], one)
            else:
                none_found.add(x["id"])
            pr.tick(i, x["name"][:50])

    rows = []
    for x in docs:
        if x["id"] in arts:
            rows += flatten(arts[x["id"]], d)
    save("cells.json", rows)
    with open(os.path.join(out, "cells.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["doc", "form", "rec", "field", "value", "page", "box", "url"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    filled = [r for r in rows if r["value"] not in (None, "")]
    print(f"{title}: {len(arts)} of {len(docs)} documents with extraction, {len(rows):,} fields "
          f"({len(filled):,} filled, {sum(1 for r in filled if r['url']):,} with viewer links, "
          f"{sum(1 for r in filled if r['box']):,} with a highlight box)", flush=True)

    anch, tax_missing = {}, []
    if anchoring:
        pr = Progress("anchoring records", len(docs))
        for i, x in enumerate(docs, 1):
            p = os.path.join(out, "tax", x["id"] + ".json")
            t = json.load(open(p, encoding="utf-8")) if (not refresh and os.path.exists(p) and os.path.getsize(p)) else None
            if t is None:
                t = fetch(f"/v2/dataroom/taxonomies/{x['id']}", env, wait=2)
                if t is not None:
                    with open(p, "w", encoding="utf-8") as fh:
                        json.dump(t, fh)
            if isinstance(t, list):
                anch[x["id"]] = [{"ledger": y.get("ledgerType"), "status": y.get("status"), "tx": y.get("transactionPointer"),
                                  "checksum": y.get("documentChecksum"), "algo": y.get("documentChecksumAlgo"),
                                  "at": y.get("updatedAt") or y.get("createdAt"), "link": y.get("documentShortLink"),
                                  "id": y.get("id")} for y in t]
            else:
                tax_missing.append(x["name"])
            pr.tick(i)
        save("anchoring.json", anch)
        n_ok = sum(1 for v in anch.values() if any(r["status"] == "Succeed" for r in v))
        print(f"anchoring: {n_ok} of {len(docs)} documents anchored, {sum(len(v) for v in anch.values())} ledger records", flush=True)

    problems = []
    if tax_missing:
        problems.append(f"{len(tax_missing)} documents without an anchoring response")
    if problems:
        print("INCOMPLETE: " + "; ".join(problems) + ". Rerun the same command to fill the gaps.", file=sys.stderr)
        return 3
    print(f'done. next: python3 tools/deal_summary.py "deals/{slug}"   (inventory + extraction + anchoring)')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
