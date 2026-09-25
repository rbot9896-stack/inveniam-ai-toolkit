#!/usr/bin/env python3
"""Pull ANY deal from the Inveniam API: deal record, folders, documents, every
extracted field (flattened to cells.json / cells.csv) and on-chain anchoring
records per document. Cross-platform, standard library only.

    cd ~/dev/inveniam
    python3 tools/fetch_deal.py --env sales "The Meridian"      # by title (case-insensitive substring)
    python3 tools/fetch_deal.py --env sales 26ca3be5-ac61-...   # or by deal id
    python3 tools/fetch_deal.py "Inveniam Capital"              # production (default env)
    (INV_ENV=sales also works instead of --env; on Windows use `python`)

Output goes to deals/<slug>/ next to inv.py. Calls are sequential on purpose:
parallel calls produce empty responses.
"""
import csv, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import inv  # noqa: E402

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def get_retry(path, env, tries=3, wait=5, label=""):
    for attempt in range(1, tries + 1):
        try:
            return inv.get_json(path, env)
        except Exception as e:
            if attempt == tries:
                print(f"  {label or path}: giving up after {tries} tries ({e})", file=sys.stderr)
                return None
            print(f"  empty/failed response, retrying ({attempt})")
            time.sleep(wait)


def main(argv):
    env = os.environ.get("INV_ENV", "prod")
    a = list(argv)
    if a[:1] == ["--env"]:
        env = a[1]; a = a[2:]
    if not a:
        sys.exit("usage: fetch_deal.py [--env sales] <deal id | title substring>")
    q = a[0]

    if UUID.match(q):
        deal = inv.get_json(f"/v2/deals/{q}", env); d, title = q, deal["title"]
    else:
        items = inv.get_json("/v2/deals?page=1&limit=100", env)["items"]
        m = [i for i in items if q.lower() in (i.get("title") or "").lower()]
        if not m:
            sys.exit("no deal title contains: " + q)
        if len(m) > 1:
            sys.exit("ambiguous, matches: " + "; ".join(i["title"] for i in m))
        d, title = m[0]["id"], m[0]["title"]
        deal = inv.get_json(f"/v2/deals/{d}", env)

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    out = os.path.join(ROOT, "deals", slug); os.makedirs(os.path.join(out, "tax"), exist_ok=True)
    print(f"deal: {title} ({d}) env: {env} -> {out}")

    def save(name, obj): json.dump(obj, open(os.path.join(out, name), "w", encoding="utf-8"))
    print("deal ..");      save("deal.json", deal)
    print("folders ..");   folders = inv.get_json(f"/v2/dataroom/deals/{d}/folders?page=1&limit=100", env); save("folders.json", folders)
    print("documents .."); docs = inv.get_json(f"/v2/dataroom/deals/{d}/documents?page=1&limit=100", env); save("docs.json", docs)
    print("artifacts .. (20-40 s)")
    arts = get_retry(f"/v2/dataroom/datalab-provider/{d}/artifacts?page=1&limit=100", env, label="artifacts")
    if arts is None:
        print("artifacts still empty after 3 tries — writing an empty list; rerun later", file=sys.stderr)
        arts = {"items": [], "meta": {}}
    save("artifacts_all.json", arts)

    rows = []
    for it in arts["items"]:
        s = it["sourceAttributes"]; doc = s["documentName"]; did = s["documentid"]
        for f in it["extractedData"]["forms"]:
            meta = {m["fieldId"]: m["fieldName"] for m in f["records"].get("extractedFieldMetaData", [])}
            for rec in f["records"].get("extractedFieldData", []):
                for fd in rec["fieldData"]:
                    loc = fd.get("fieldLocations") or [{}]
                    rows.append(dict(doc=doc, docId=did, ctype=s["contentType"], form=f["formName"], rec=rec["recordSequence"],
                                     field=meta.get(fd["fieldId"], fd.get("fieldQueryName")), value=fd.get("value"),
                                     page=loc[0].get("Page"), url=(fd.get("sourceAttributes") or {}).get("fieldPreviewURL")))
    save("cells.json", rows)
    with open(os.path.join(out, "cells.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["doc", "form", "rec", "field", "value", "page"]); w.writeheader()
        for r in rows: w.writerow({k: r[k] for k in w.fieldnames})
    print(f"{title}: {len(docs['items'])} documents, {len(folders['items'])} folders, {len(arts['items'])} artifacts, "
          f"{len(rows)} cells, {sum(1 for r in rows if r['url'])} with viewer links")

    print(f"anchoring records (taxonomies, ~{len(docs['items'])} calls) ..")
    res = {}
    for x in docs["items"]:
        t = get_retry(f"/v2/dataroom/taxonomies/{x['id']}", env, wait=2, label=x["name"])
        if t is None: continue
        json.dump(t, open(os.path.join(out, "tax", f"{x['id']}.json"), "w", encoding="utf-8"))
        if isinstance(t, list):
            res[x["id"]] = [{"ledger": y["ledgerType"], "status": y["status"], "tx": y["transactionPointer"],
                             "checksum": y["documentChecksum"], "algo": y["documentChecksumAlgo"],
                             "at": y["updatedAt"] or y["createdAt"], "link": y["documentShortLink"], "id": y["id"]} for y in t]
    save("anchoring.json", res)
    print(f"{len(res)} documents with anchoring records, {sum(len(v) for v in res.values())} ledger records")
    print(f'done. next: python3 tools/deal_summary.py "deals/{slug}"   (inventory + anchoring + extraction overview)')


if __name__ == "__main__":
    main(sys.argv[1:])
