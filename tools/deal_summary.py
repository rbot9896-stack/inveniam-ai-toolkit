"""Summarise a pulled deal folder (from tools/fetch_deal.sh): data-room inventory,
extraction coverage and on-chain anchoring per document.

  python3 tools/deal_summary.py deals/<slug>            # prints a Markdown summary
  python3 tools/deal_summary.py deals/<slug> --json     # machine-readable

Works for any deal in any environment. Standard library only.
"""
import json, os, sys, collections

if len(sys.argv) < 2: sys.exit(__doc__)
D = sys.argv[1]; as_json = '--json' in sys.argv
def load(name, default):
    p = os.path.join(D, name)
    return json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else default

deal = load('deal.json', {}); folders = load('folders.json', {'items': []})['items']
docs = load('docs.json', {'items': []})['items']; cells = load('cells.json', []); anch = load('anchoring.json', {})
fmap = {f['id']: f['name'] for f in folders}
fields = collections.Counter(r['docId'] for r in cells)
linked = collections.Counter(r['docId'] for r in cells if r.get('url'))
ctype = {r['docId']: r['ctype'] for r in cells}

rows = []
for x in docs:
    a = anch.get(x['id'], [])
    rows.append({'folder': fmap.get(x['folderId'], '?'), 'name': x['name'], 'id': x['id'], 'contentType': ctype.get(x['id']),
                 'fields': fields.get(x['id'], 0), 'linkedFields': linked.get(x['id'], 0),
                 'anchored': any(r['status'] == 'Succeed' for r in a),
                 'ledgers': sorted(r['ledger'] for r in a if r['status'] == 'Succeed'),
                 'pending': sorted(r['ledger'] for r in a if r['status'] == 'Pending'),
                 'checksum': a[0]['checksum'] if a else None})
summary = {'deal': {'id': deal.get('id'), 'title': deal.get('title'), 'type': (deal.get('dealType') or {}).get('name'), 'status': deal.get('status')},
           'documents': len(docs), 'folders': len(folders), 'documentsWithExtraction': sum(1 for r in rows if r['fields']),
           'extractedFields': len(cells), 'fieldsWithViewerLinks': sum(1 for r in cells if r.get('url')),
           'documentsAnchored': sum(1 for r in rows if r['anchored']),
           'ledgerRecords': sum(len(v) for v in anch.values()),
           'ledgers': sorted({l for r in rows for l in r['ledgers'] + r['pending']}),
           'rows': rows}
if as_json: print(json.dumps(summary, indent=1)); sys.exit()

s = summary['deal']
print(f"# {s['title']} — {s['type']} · {s['status']}\n")
print(f"{summary['documents']} documents in {summary['folders']} folders · "
      f"{summary['documentsWithExtraction']} with extracted data ({summary['extractedFields']:,} fields, {summary['fieldsWithViewerLinks']:,} with viewer links) · "
      f"{summary['documentsAnchored']} anchored on-chain ({summary['ledgerRecords']} ledger records across {', '.join(summary['ledgers']) or 'none'})\n")
print("| Folder | Document | Type | Fields | Anchored on |\n|---|---|---|---:|---|")
for r in sorted(rows, key=lambda r: (r['folder'], r['name'])):
    anchored = ('✓ ' + ', '.join(r['ledgers']) + (f" (pending: {', '.join(r['pending'])})" if r['pending'] else '')) if r['anchored'] else '—'
    print(f"| {r['folder']} | {r['name']} | {r['contentType'] or ''} | {r['fields'] or ''} | {anchored} |")
print("\nForms extracted per document type:")
forms = collections.defaultdict(set)
for r in cells: forms[r['ctype']].add(r['form'])
for ct in sorted(forms): print(f"- {ct}: {', '.join(sorted(forms[ct]))}")
