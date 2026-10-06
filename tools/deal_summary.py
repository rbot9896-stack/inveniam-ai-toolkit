"""Summarise a pulled deal folder (from tools/fetch_deal.py): data-room inventory,
extraction coverage (filled fields, viewer links, highlight boxes) and on-chain
anchoring per document.

  python3 tools/deal_summary.py deals/<slug>            # prints a Markdown summary
  python3 tools/deal_summary.py deals/<slug> --json     # machine-readable

Works for any deal in any environment. Standard library only.
"""
import json, os, sys, collections

if len(sys.argv) < 2: sys.exit(__doc__)
D = sys.argv[1]; as_json = '--json' in sys.argv
def load(name, default):
    p = os.path.join(D, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) and os.path.getsize(p) else default

deal = load('deal.json', {}); folders = load('folders.json', {'items': []})['items']
docs = load('docs.json', {'items': []})['items']; cells = load('cells.json', []); anch = load('anchoring.json', {})
fmap = {f['id']: f['name'] for f in folders}
filled = [r for r in cells if r.get('value') not in (None, '')]
n_fields = collections.Counter(r['docId'] for r in cells)
n_filled = collections.Counter(r['docId'] for r in filled)
n_box = collections.Counter(r['docId'] for r in filled if r.get('box'))
ctype = {r['docId']: r['ctype'] for r in cells}

rows = []
for x in docs:
    a = anch.get(x['id'], [])
    rows.append({'folder': fmap.get(x.get('folderId'), '?'), 'name': x['name'], 'id': x['id'], 'contentType': ctype.get(x['id']),
                 'fields': n_fields.get(x['id'], 0), 'filled': n_filled.get(x['id'], 0), 'highlighted': n_box.get(x['id'], 0),
                 'anchored': any(r['status'] == 'Succeed' for r in a),
                 'ledgers': sorted(r['ledger'] for r in a if r['status'] == 'Succeed'),
                 'pending': sorted(r['ledger'] for r in a if r['status'] == 'Pending'),
                 'failed': sorted(r['ledger'] for r in a if r['status'] == 'Failed'),
                 'checksum': a[0]['checksum'] if a else None})
summary = {'deal': {'id': deal.get('id'), 'title': deal.get('title'), 'type': (deal.get('dealType') or {}).get('name'), 'status': deal.get('status')},
           'documents': len(docs), 'folders': len(folders), 'documentsWithExtraction': sum(1 for r in rows if r['fields']),
           'extractedFields': len(cells), 'filledFields': len(filled),
           'filledWithViewerLinks': sum(1 for r in filled if r.get('url')),
           'filledWithHighlight': sum(1 for r in filled if r.get('box')),
           'linksBuiltFromIds': sum(1 for r in filled if r.get('built')),
           'documentsAnchored': sum(1 for r in rows if r['anchored']),
           'ledgerRecords': sum(len(v) for v in anch.values()),
           'ledgers': sorted({l for r in rows for l in r['ledgers'] + r['pending'] + r['failed']}),
           'rows': rows}
if as_json: print(json.dumps(summary, indent=1)); sys.exit()

try:
    s = summary['deal']
    print(f"# {s['title']} — {s['type']} · {s['status']}\n")
    print(f"{summary['documents']} documents in {summary['folders']} folders · "
          f"{summary['documentsWithExtraction']} with extracted data · "
          f"{summary['documentsAnchored']} anchored on-chain ({summary['ledgerRecords']} ledger records across {', '.join(summary['ledgers']) or 'none'})\n")
    print(f"Fields: {summary['extractedFields']:,} extracted, {summary['filledFields']:,} with a value, "
          f"{summary['filledWithViewerLinks']:,} of those open in the viewer, {summary['filledWithHighlight']:,} with a highlight box"
          + (f" ({summary['linksBuiltFromIds']:,} links built from ids for hand-set values)" if summary['linksBuiltFromIds'] else "") + "\n")
    print("| Folder | Document | Type | Filled / fields | Highlighted | Anchored on |\n|---|---|---|---:|---:|---|")
    for r in sorted(rows, key=lambda r: (r['folder'], r['name'])):
        led = ', '.join(r['ledgers'])
        if r['pending']: led += f" (pending: {', '.join(r['pending'])})"
        if r['failed']: led += f" (failed: {', '.join(r['failed'])})"
        anchored = ('✓ ' + led) if r['anchored'] else ('— ' + led).strip()
        fill = f"{r['filled']} / {r['fields']}" if r['fields'] else 'no extraction'
        print(f"| {r['folder']} | {r['name']} | {r['contentType'] or ''} | {fill} | {r['highlighted'] if r['fields'] else ''} | {anchored} |")
    print("\nForms extracted per document type:")
    forms = collections.defaultdict(set)
    for r in cells: forms[r['ctype']].add(r['form'])
    for ct in sorted(forms, key=str): print(f"- {ct}: {', '.join(sorted(forms[ct]))}")
except BrokenPipeError:          # e.g. piped into head
    pass
