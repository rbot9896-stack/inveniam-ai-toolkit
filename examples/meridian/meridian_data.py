"""Select the cells the Meridian dashboard needs.
Reads  ../../deals/the-meridian/{cells,docs,folders,deal,anchoring}.json  ->  writes data.json there
(pull first with: python3 tools/fetch_deal.py --env sales "The Meridian")
Each figure is {v: value, u: fieldPreviewURL, p: page, d: documentId}.
Then run build_meridian.py. Worked example of API-PLAYBOOK recipes C, D and E.
"""
import json, re, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'deals', 'the-meridian')
rows = json.load(open(f'{B}/cells.json'))
docs = json.load(open(f'{B}/docs.json'))['items']
folders = json.load(open(f'{B}/folders.json'))['items']
deal = json.load(open(f'{B}/deal.json'))

def cell(docpre, form, field, rec='0'):
    for r in rows:
        if r['doc'].startswith(docpre) and r['form'] == form and r['field'] == field and str(r['rec']) == str(rec):
            return {'v': r['value'], 'u': r['url'], 'p': r['page'], 'd': r['docId']}
    return None

def rowsof(docpre, form):
    out = {}
    for r in rows:
        if r['doc'].startswith(docpre) and r['form'] == form:
            out.setdefault(str(r['rec']), {})[r['field']] = {'v': r['value'], 'u': r['url'], 'p': r['page'], 'd': r['docId']}
    return [out[k] for k in sorted(out, key=int)]

Q = [('Q3 2025', '01_', '12_', '16_', '20_'), ('Q4 2025', '02_', '13_', '17_', '21_'),
     ('Q1 2026', '03_', '14_', '18_', '22_'), ('Q2 2026', '04_', '15_', '19_', '23_')]
A = '04_'  # latest appraisal

d = {'deal': {'id': deal['id'], 'title': deal['title'], 'symbol': deal['dealSymbol'], 'status': deal['status'],
              'description': deal['description'], 'image': deal['image'], 'type': deal['dealType']['name']}}

d['kpi'] = {k: cell(A, f, k) for f, k in [
    ('Valuation Summary', 'Value Conclusion'), ('Valuation Summary', 'Value Cap Rate'),
    ('Valuation Summary', 'Final Valuation PSF (Current Quarter)'), ('Valuation Summary', 'Effective Date'),
    ('Valuation Summary', 'Valuation Methodology'), ('Valuation Summary', 'Value Premise'),
    ('Building Summary', 'Net Rentable Area'), ('Building Summary', 'Occupancy Rate'), ('Building Summary', 'Number of Units'),
    ('Building Summary', 'Year Built'), ('Building Summary', 'Year Renovated'), ('Building Summary', 'Number of Stories'),
    ('Building Summary', 'Building Condition'), ('Building Summary', 'Building Use Type'),
    ('Tenant Concentration', 'WALT Current Quarter'), ('Tenant Concentration', 'Largest Tenant'), ('Tenant Concentration', 'Largest Tenant (SF)'),
    ('Appraisal Background', 'Address'), ('Appraisal Background', 'Prepared By'), ('Appraisal Background', 'Prepared For'),
    ('Appraisal Background', 'Appraiser Name'), ('Appraisal Background', 'Date of Report'),
    ('Underwriting Assumptions', 'IRR Rate'), ('Underwriting Assumptions', 'Discount Rate'),
    ('Underwriting Assumptions', 'Terminal Capitalization Rate'), ('Underwriting Assumptions', 'Vacancy Loss'),
    ('Underwriting Assumptions', 'Model Assumptions - Hold Period (Current Quarter)'),
    ('Tax Summary', 'Assessed Value'), ('Tax Summary', 'Current Tax Liability'), ('Tax Summary', 'Tax Year'),
    ('Market Submarket Summary', 'Market Submarket')]}

# ---- quarterly trend ----
d['quarters'] = []
for q, ap, inc, bs, rr in Q:
    cols = [r['field'] for r in rows if r['doc'].startswith(inc) and r['form'].startswith('Income Statement') and r['field'].startswith('TTM')]
    ttm = cols[0] if cols else 'TTM'
    isr = {x['Line Item']['v']: x for x in rowsof(inc, 'Income Statement - Page 1 Group 1') if x.get('Line Item')}
    def isv(name):
        x = isr.get(name)
        return x.get(ttm) if x else None
    d['quarters'].append({'q': q,
        'value': cell(ap, 'Valuation Summary', 'Value Conclusion'), 'cap': cell(ap, 'Valuation Summary', 'Value Cap Rate'),
        'psf': cell(ap, 'Valuation Summary', 'Final Valuation PSF (Current Quarter)'),
        'occ': cell(ap, 'Building Summary', 'Occupancy Rate'), 'walt': cell(ap, 'Tenant Concentration', 'WALT Current Quarter'),
        'rev': isv('Total Revenue'), 'opex': isv('Total Operating Expenses'), 'noi': isv('Net Operating Income (NOI)'),
        'ni': isv('Net Income'), 'cfads': isv('Cash Flow After Debt Service (CFADS)'), 'dist': isv('Distribution to Members'),
        'int': isv('Interest Expense'),
        'assets': cell(bs, 'Summary', 'Total Assets'), 'cash': cell(bs, 'Summary', 'Cash'), 'debt': cell(bs, 'Summary', 'Debt'),
        'equity': cell(bs, 'Summary', 'Total Equity'), 'liab': cell(bs, 'Summary', 'Total Liabilities'),
        'period': cell(inc, 'Summary', 'Reporting Period'), 'ttm_col': ttm})

# ---- Q2 2026 income statement, full ----
isrows = rowsof('15_', 'Income Statement - Page 1 Group 1')
months = [f for f in isrows[1] if f != 'Line Item' and not f.startswith('TTM')]
d['is_months'] = months
d['is'] = [{'item': x['Line Item']['v'], 'ttm': x.get('TTM Total MY-2025-2026'), 'm': [x.get(m) for m in months]}
           for x in isrows if x.get('Line Item')]

# ---- Q2 2026 balance sheet ----
bsrows = rowsof('19_', 'Balance Sheet - Page 1 Group 1')
bcols = [f for f in bsrows[1] if f != 'Line Item']
d['bs_cols'] = bcols
d['bs'] = [{'item': x['Line Item']['v'], 'm': [x.get(c) for c in bcols]} for x in bsrows if x.get('Line Item')]

# ---- rent roll + leases ----
def norm(s): return re.sub(r'[^a-z]', '', (s or '').lower().replace('&', 'and'))[:14]
leases = {}
for pre in ['05_', '06_', '07_', '08_', '09_', '10_', '11_']:
    info = rowsof(pre, 'Lease Information'); sched = rowsof(pre, 'Rent Schedule')
    if not info: continue
    t = info[0]['Tenant Name']['v']
    cur = None
    for s in sched:
        per = s.get('Base Rent Period', {}).get('v') or ''
        m = re.findall(r'(\d\d)/(\d\d)/(\d{4})', per)
        if len(m) == 2:
            a = (int(m[0][2]), int(m[0][0]), int(m[0][1])); b = (int(m[1][2]), int(m[1][0]), int(m[1][1]))
            if a <= (2026, 6, 30) <= b: cur = s
    leases[norm(t)] = {'info': info[0], 'schedule': sched, 'current': cur,
                       'doc': [x for x in docs if x['name'].startswith(pre)][0]['id']}
d['tenants'] = []
for x in rowsof('23_', 'Rent Roll Details'):
    t = x['Tenant Name']['v']
    d['tenants'].append({'unit': x.get('Unit Number'), 'tenant': x.get('Tenant Name'), 'sf': x.get('Unit Size'),
                         'start': x.get('Lease Date'), 'end': x.get('Lease Expiration Date'), 'lease': leases.get(norm(t))})
d['rr_period'] = cell('23_', 'Rent Roll Background', 'Document Period')
d['rr_hist'] = [{'q': q, 'rows': [{'tenant': x.get('Tenant Name'), 'sf': x.get('Unit Size'), 'unit': x.get('Unit Number')}
                                  for x in rowsof(rr, 'Rent Roll Details')]} for q, ap, inc, bs, rr in Q]

# ---- loan ----
d['loan'] = {}
for r in rows:
    if r['ctype'] == 'CREDIT_AGREEMENT' and r['value'] not in (None, ''):
        d['loan'][r['field']] = {'v': r['value'], 'u': r['url'], 'p': r['page'], 'd': r['docId'], 'form': r['form']}

# ---- appraisal projections + comps ----
d['noi_proj'] = [{'period': x.get('Summary Type'), 'gi': x.get('Gross Income'), 'exp': x.get('Total Expenses'),
                  'noi': x.get('Net Operating Income (NOI)')} for x in rowsof(A, 'Income Summary')]
d['comps'] = [{k.replace('Sales Comp. ', ''): v for k, v in x.items()} for x in rowsof(A, 'Sales Comparables')]

# ---- data room inventory ----
artcount = {}
for r in rows: artcount[r['docId']] = artcount.get(r['docId'], 0) + 1
fmap = {f['id']: f['name'] for f in folders}
d['dataroom'] = [{'folder': fmap.get(x['folderId'], '?'), 'name': x['name'], 'id': x['id'],
                  'fields': artcount.get(x['id'], 0), 'created': x['createdAt']} for x in docs]
# ---- on-chain anchoring (taxonomy records, one per ledger) ----
anch = json.load(open(f'{B}/anchoring.json')) if os.path.exists(f'{B}/anchoring.json') else {}
for x in d['dataroom']:
    recs = anch.get(x['id'], [])
    x['anchoring'] = sorted(recs, key=lambda r: (r['status'] != 'Succeed', r['ledger']))
    x['anchored'] = any(r['status'] == 'Succeed' for r in recs)
    x['pending'] = sum(1 for r in recs if r['status'] == 'Pending')
d['anchor_stats'] = {'docs_anchored': sum(1 for x in d['dataroom'] if x['anchored']),
                     'records': sum(len(x['anchoring']) for x in d['dataroom']),
                     'succeed': sum(1 for x in d['dataroom'] for r in x['anchoring'] if r['status'] == 'Succeed'),
                     'pending': sum(x['pending'] for x in d['dataroom']),
                     'ledgers': sorted({r['ledger'] for x in d['dataroom'] for r in x['anchoring']})}
d['stats'] = {'docs': len(docs), 'folders': len(folders), 'artifact_docs': len(artcount), 'cells': len(rows),
              'linked': sum(1 for r in rows if r['url'])}
# ---- data-quality flags: Summary form vs the statement's own detail table ----
import datetime
def parse_col(c):
    try: return datetime.datetime.strptime(c.replace('As of ', ''), '%B %d, %Y')
    except Exception: return None
def numv(s):
    if s in (None, ''): return None
    t = re.sub(r'[$,%\s]', '', str(s)); t = re.sub(r'^\((.*)\)$', r'-\1', t)
    try: return float(t)
    except Exception: return None
d['flags'] = []
for q, ap, inc, bs, rr in Q:
    det = {x['Line Item']['v']: x for x in rowsof(bs, 'Balance Sheet - Page 1 Group 1') if x.get('Line Item')}
    if not det: continue
    cols = sorted([c for c in det['TOTAL ASSETS'] if parse_col(c)], key=parse_col)
    last = cols[-1]
    for sk, dk, key in [('Total Assets', 'TOTAL ASSETS', 'assets'), ('Cash', 'Cash and Cash Equivalents', 'cash'),
                        ('Total Liabilities', 'TOTAL LIABILITIES', 'liab'), ('Total Equity', "TOTAL MEMBERS' EQUITY", 'equity'), ('Debt', 'Mortgage Note Payable', 'debt')]:
        sc = cell(bs, 'Summary', sk); dc = det.get(dk, {}).get(last)
        if not sc or not dc or numv(sc['v']) is None or numv(dc['v']) is None or numv(sc['v']) == numv(dc['v']): continue
        # which column does the summary value actually match?
        src = next((c for c in cols if numv(det[dk].get(c, {}).get('v')) == numv(sc['v'])), None)
        d['flags'].append({'q': q, 'key': key, 'field': sk, 'summary': sc, 'detail': dc, 'detail_col': last.replace('As of ', ''),
                           'matches_col': src.replace('As of ', '') if src else None,
                           'asof': cell(bs, 'Summary', 'As of Date')})
json.dump(d, open(f'{B}/data.json', 'w'))
print('ok', {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()}, os.path.getsize(f'{B}/data.json'), 'bytes')
