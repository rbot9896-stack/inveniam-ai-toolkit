#!/usr/bin/env bash
# Pull ANY deal from the Inveniam API: deal record, folders, documents, every
# extracted field (flattened to cells.json/cells.csv) and on-chain anchoring
# records per document.
#
#   cd ~/dev/inveniam
#   INV_ENV=sales bash tools/fetch_deal.sh "The Meridian"        # by title (case-insensitive substring)
#   INV_ENV=sales bash tools/fetch_deal.sh 26ca3be5-ac61-...     # or by deal id
#   bash tools/fetch_deal.sh "Inveniam Capital"                  # production (default env)
#
# Output goes to ~/dev/inveniam/deals/<slug>/ . Requires ./inv.sh and the
# environment's .env file beside it. Sequential on purpose: parallel inv.sh
# calls from one shell produce empty responses.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INV="$ROOT/inv.sh"
export INV_ENV="${INV_ENV:-prod}"
Q="${1:-}"; [ -n "$Q" ] || { echo "usage: fetch_deal.sh <deal id | title substring>" >&2; exit 1; }

# resolve deal id
if [[ "$Q" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  D="$Q"; TITLE=$("$INV" GET "/v2/deals/$D" | python3 -c 'import sys,json;print(json.load(sys.stdin)["title"])')
else
  read -r D TITLE < <("$INV" GET "/v2/deals?page=1&limit=100" | python3 -c '
import sys,json; q=sys.argv[1].lower(); items=json.load(sys.stdin)["items"]
m=[i for i in items if q in (i.get("title") or "").lower()]
if not m: sys.exit("no deal title contains: "+sys.argv[1])
if len(m)>1: sys.exit("ambiguous, matches: "+"; ".join(i["title"] for i in m))
print(m[0]["id"], m[0]["title"])' "$Q")
fi
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g')
OUT="$ROOT/deals/$SLUG"; mkdir -p "$OUT"
echo "deal: $TITLE ($D) env: $INV_ENV -> $OUT"

echo "deal ..";      "$INV" GET "/v2/deals/$D" > "$OUT/deal.json"
echo "folders ..";   "$INV" GET "/v2/dataroom/deals/$D/folders?page=1&limit=100" > "$OUT/folders.json"
echo "documents .."; "$INV" GET "/v2/dataroom/deals/$D/documents?page=1&limit=100" > "$OUT/docs.json"
echo "artifacts .. (20-40 s)"
for attempt in 1 2 3; do
  "$INV" GET "/v2/dataroom/datalab-provider/$D/artifacts?page=1&limit=100" > "$OUT/artifacts_all.json" 2>/dev/null || true
  [ -s "$OUT/artifacts_all.json" ] && break
  echo "  empty response, retrying ($attempt)"; sleep 5
done
[ -s "$OUT/artifacts_all.json" ] || { echo "artifacts still empty after 3 tries — writing an empty list; rerun later" >&2; echo '{"items":[],"meta":{}}' > "$OUT/artifacts_all.json"; }

python3 - "$OUT" <<'EOF'
import json, csv, sys
out = sys.argv[1]
a = json.load(open(f'{out}/artifacts_all.json'))
rows = []
for it in a['items']:
    s = it['sourceAttributes']; doc = s['documentName']; did = s['documentid']
    for f in it['extractedData']['forms']:
        meta = {m['fieldId']: m['fieldName'] for m in f['records'].get('extractedFieldMetaData', [])}
        for rec in f['records'].get('extractedFieldData', []):
            for fd in rec['fieldData']:
                loc = fd.get('fieldLocations') or [{}]
                rows.append(dict(doc=doc, docId=did, ctype=s['contentType'], form=f['formName'], rec=rec['recordSequence'],
                                 field=meta.get(fd['fieldId'], fd.get('fieldQueryName')), value=fd.get('value'),
                                 page=loc[0].get('Page'), url=(fd.get('sourceAttributes') or {}).get('fieldPreviewURL')))
json.dump(rows, open(f'{out}/cells.json', 'w'))
w = csv.DictWriter(open(f'{out}/cells.csv', 'w'), fieldnames=['doc', 'form', 'rec', 'field', 'value', 'page']); w.writeheader()
for r in rows: w.writerow({k: r[k] for k in w.fieldnames})
docs = json.load(open(f'{out}/docs.json'))['items']; folders = json.load(open(f'{out}/folders.json'))['items']
print(f"{json.load(open(f'{out}/deal.json'))['title']}: {len(docs)} documents, {len(folders)} folders, "
      f"{len(a['items'])} artifacts, {len(rows)} cells, {sum(1 for r in rows if r['url'])} with viewer links")
EOF

echo "anchoring records (taxonomies, ~30 calls) .."
mkdir -p "$OUT/tax"
for id in $(python3 -c "import json;[print(x['id']) for x in json.load(open('$OUT/docs.json'))['items']]"); do
  for attempt in 1 2 3; do
    "$INV" GET "/v2/dataroom/taxonomies/$id" > "$OUT/tax/$id.json" 2>/dev/null || true
    [ -s "$OUT/tax/$id.json" ] && break; sleep 2
  done
done
python3 - "$OUT" <<'PYEOF'
import json, glob, os, sys
out = sys.argv[1]; res = {}
for f in glob.glob(f'{out}/tax/*.json'):
    did = os.path.basename(f)[:-5]
    try: t = json.load(open(f))
    except Exception: continue
    if not isinstance(t, list): continue
    res[did] = [{'ledger': x['ledgerType'], 'status': x['status'], 'tx': x['transactionPointer'], 'checksum': x['documentChecksum'],
                 'algo': x['documentChecksumAlgo'], 'at': x['updatedAt'] or x['createdAt'], 'link': x['documentShortLink'], 'id': x['id']} for x in t]
json.dump(res, open(f'{out}/anchoring.json', 'w'))
print(f"{len(res)} documents with anchoring records, {sum(len(v) for v in res.values())} ledger records")
PYEOF

echo "done. next: python3 $ROOT/tools/deal_summary.py \"$OUT\"   (inventory + anchoring + extraction overview)"
