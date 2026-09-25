# Inveniam API playbook — for the assistant

Read this once setup (START-HERE.md) is complete, together with
`skill/inveniam/SKILL.md` (the platform skill: resource model, workflow rules,
provisioning quirks, tool-name mapping; maintained at
https://github.com/aberdellans/Agent_skill). It is your working reference
for anything involving the Inveniam platform: how to call the API, what comes
back, the quirks that waste calls, and step-by-step recipes for the things
people ask for. Last verified 2026-09-24. Canonical copy: https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/API-PLAYBOOK.md (repo https://github.com/rbot9896-stack/inveniam-ai-toolkit).

---

## 1. Making a call

All calls go through `inv.py` (or its wrapper `inv.sh`) in the connected folder (`~/mnt/inveniam` in
Cowork's shell). It exchanges key + token for a short-lived JWT, caches it ~50
minutes per environment, and adds the headers. You never see credential values.

```
cd ~/mnt/inveniam
python3 inv.py GET "/v2/deals?page=1&limit=100"           # production (.env)   (Windows: python inv.py …)
python3 inv.py --env sales GET "/v2/deals?page=1&limit=100"   # sales (.env.sales); INV_ENV=sales also works
python3 inv.py POST "/v2/dataroom/file-veracity/initiate" -d '{"fileId":"…"}'   # -d implies JSON; -H "k: v" and -o FILE also supported
```

Under the hood: `GET /v2/api-keys/auth/token` with headers `x-api-key: <key>`
and `Authorization: <token>` → `{"token": <jwt>}`; every call then sends
`Authorization: Bearer <jwt>` and `x-api-key`.

| | Production | Sales / demo |
|---|---|---|
| REST base | `https://api.inveniam.app` | `https://slsus01-api.inveniam.app` |
| Viewer host to use in links | `icp.inveniam.io` (API says `icp-v1`) | `sales.inveniam.io` (API says `sales-v1`) |
| MCP connector | ask Ryder | `https://sales-api.inveniam.io/mcp` (connector only; host not allowlisted for direct calls) |
| Content | real, confidential | 17 demo deals, shareable |
| Spec | `GET /v2/api/docs/swagger-ui-init.js` (~640 KB — grep it; `/v2/api/docs-json` is 403) | same path |

Working rules:
- **Sequential calls only.** Parallel `inv.py` calls from one shell return empty bodies.
- **Page.** `limit` ≤ 100; responses are `{items, meta}`; production `/v2/deals` at 100 is ~50K chars — filter before printing.
- **Empty 200s happen.** Retry after a few seconds; if one document stays empty, report it rather than treating it as missing.
- **Long commands fail in Cowork** (`spawn E2BIG` above ~6 KB). Write a script file, then run it.
- **Downloads are working copies.** Extract, then delete. Inveniam's model is virtualised access, not copies.
- **Credentials never leave the `.env` files.** Not into the cloud workspace, a page, memory, or chat.
- **Destructive or permission-changing calls** (delete deal/portfolio/comment, role and permission changes): describe exactly what will change, get explicit approval, then call. The REST API has no safety gate.

## 2. Resource model

```
Portfolio → Deal → Folder → Document
                 ├─ Data artifacts   (every field extracted from a document, with source location)
                 ├─ Taxonomies       (classification + on-chain anchoring records per document)
                 └─ Workflows        (tasks → checklists, RACI, comments)
```
Almost everything is scoped by `dealId`. Get ids from list calls; never guess.

## 3. Endpoints

| Purpose | Endpoint | What to know |
|---|---|---|
| Deals | `GET /v2/deals?page=&limit=` · `GET /v2/deals/{dealId}` | items carry `id`, `title`, `type` (real-estate / fund / debt), `status`, `price`, `dealSymbol`, `portfolioId`; full record adds `description`, `dealType.name`, `image` |
| Portfolios | `GET /v2/portfolios` | |
| Folders | `GET /v2/dataroom/deals/{dealId}/folders?page=&limit=` | `id`, `name`, `parentId` |
| Documents | `GET /v2/dataroom/deals/{dealId}/documents?page=&limit=` | `id`, `name`, `folderId`, `path`, `status`, `version`, `createdAt` |
| Download | `GET /v2/dataroom/download-file/{documentId}` | pass `-o file`; may arrive without a friendly name |
| **All extracted fields for a deal** | `GET /v2/dataroom/datalab-provider/{dealId}/artifacts?page=1&limit=100` | one call for the whole deal (~20 s). Use this, not the per-document loop |
| One document's extraction | `GET /v2/dataroom/datalab-provider/{dealId}/artifacts/{documentId}` | ~19 s each |
| **Anchoring / taxonomy** | `GET /v2/dataroom/taxonomies/{documentId}` | array, one record per ledger — see §5 |
| File by hash | `GET /v2/files/by-checksum?hash=<sha256>` | finds a file from a checksum shown in the UI's DLT panel |
| Integrity check | `POST /v2/dataroom/file-veracity/initiate` `{fileId|taxonomyId|artifactId}` → `GET /v2/dataroom/file-veracity/status/{jobId}` | async; checks existence, taxonomy consistency, ledger verification, extraction validity |
| Datalab config | `GET /v2/datalab/document-types` · `/extraction/templates` · `/extraction/fields` | which document types and fields the extractor knows |
| Mongo connector status | `GET /v2/datalab/{dealId}/mongo-connection-status` | org-level external Mongo *output* connector; 403 on a sales Manager key |
| Workflows | `GET /v2/deals/{dealId}/workflows`, `…/tasks`, `GET /v2/workflows/tasks/{taskId}`, status/RACI/comment endpoints | see §6 |
| Data-room writes | create folders, upload files | **no move, rename or delete via API** — UI only. `update_deal` can't change price; description caps ~1,500 chars |

Viewer links: whole document `https://<viewer>/view-file/{documentId}?id={dealId}`;
a field adds `&prev=1;{page}&formId=…&recordId=…&fieldId=…`. Rewrite the host
(§1 table) — the API returns the old one. Viewer hosts aren't reachable from
your shells; only the user's browser can open them.

## 4. Data artifacts — field-level provenance

An artifact is one document's extraction (and a MongoDB document: `_id`s
throughout — this endpoint is the only read path to that store; nothing
vector/semantic is exposed).

```
sourceAttributes: { documentid, documentName, contentType, dealId, documentPreviewURL }
extractedData.forms[]:
  formName
  records.extractedFieldMetaData[]: { fieldId, fieldName, fieldType }
  records.extractedFieldData[]:     { recordSequence, fieldData[]: {
        fieldId, value, stringValue|numberValue|dateValue…,
        fieldLocations[]: { Page, Geometry.BoundingBox },
        sourceAttributes.fieldPreviewURL } }
```

Flatten to rows `{doc, docId, contentType, form, rec, field, value, page, url}`
— `tools/fetch_deal.py` does this into `deals/<slug>/cells.json` and `.csv`.
Content types seen: APPRAISAL, INCOME_STATEMENT, BALANCE_SHEET, RENT_ROLL,
LEASE, CREDIT_AGREEMENT. Not every document has an artifact (decks, memos, cap
tables, ESA/title/zoning reports usually don't).

**Extraction can be wrong while looking right.** Example: a balance sheet's
Summary form took its totals from the January column instead of December. Before
presenting statement data, run the consistency checks in recipe C and flag
failures visibly.

## 5. On-chain anchoring

`GET /v2/dataroom/taxonomies/{documentId}` returns one record per ledger:

| Field | Meaning |
|---|---|
| `status` | `Succeed` · `Pending` · `Failed` · `Canceled` |
| `ledgerType` | Metachain, BSC, Base, Avalanche, HederaHashgraph, Mantra, NVNM, Ethereum, Polygon, Tezos, QLDB, HLFabric, Quorum, Accumulate, Provenance … |
| `transactionPointer` | tx hash (`0x…` on EVM chains) or ledger key |
| `documentChecksum` / `documentChecksumAlgo` | SHA-256 of the file |
| `documentShortLink` | link to the anchoring record |
| `createdAt` / `updatedAt` | when anchored |

A document is "anchored" if at least one record is `Succeed`. Typical pattern:
everything on Metachain, key documents additionally on several public chains.
Don't link to block explorers unless you know mainnet vs testnet — show the
pointer and the record link.

## 6. Workflows (summary — full detail in `skill/inveniam/SKILL.md`)

- Task status is one of `Open · In progress · Review · Done · On hold · Not applicable`.
  Transitions are a graph: read `allowedNextStatuses` from `get task` before
  changing; `Open → Review` needs `In progress` in between.
- `get task` reports status in `currentStatus`; the change call takes `new_status`.
- Single-task, comment, checklist and workflow-instance calls need the deal id
  as a **`deal-id` HTTP header**, not in the path — omit it and you get
  `404 "No dealId provided"`. The OpenAPI spec doesn't mention this.
- RACI buckets are Responsible / Approver / Informed, under `participants`.
  Templates bind RACI to roles; they're authored in the UI, attach-only via API.
- Comments are author-scoped: you can edit/delete only your own. Replies have `parentId`.
- No webhooks — poll.

## 7. Recipes

**A. Explore a deal.** `GET /v2/deals` (filter by title) → `GET /v2/deals/{id}`
→ folders → documents. Or `python3 tools/fetch_deal.py --env … "<title or id>"`
then `python3 tools/deal_summary.py deals/<slug>` for inventory + extraction
coverage + anchoring in one table.

**B. Answer a question with provenance.** Find the field(s) in `cells.json`
(match on `form`/`field`/`rec`), quote `value`, and give the `url` with the
viewer host rewritten. Never quote a number from extracted data without its
link.

**C. Verify statement data before presenting it.**
- Balance sheet: Summary form vs the last column of the detail table;
  Assets = Liabilities + Equity per column; asset lines sum to total; the same
  month across overlapping quarterly statements agrees.
- Income statement: months sum to TTM (allow small source rounding);
  Revenue − Opex = NOI; NOI − Depreciation − Interest = Net income.
- Rent roll / leases: SF sums to total and NRA; PSF × SF = base rent per
  schedule year; expiries agree between lease and rent roll.
- Appraisal: value / NRA = stated $/SF.
Flag every failure on the page itself (badge + explanation + links to both
values). `examples/meridian/meridian_data.py` has a working implementation of
the balance-sheet check.

**D. Anchoring audit.** Taxonomy call per document (sequential) → table of
document / ledgers Succeed / Pending / checksum. `fetch_deal.py` already saves
this as `anchoring.json`; `deal_summary.py` prints it.

**E. Provenance dashboard for any deal.** Pull (A) → select figures by
(document, form, field, record) into `{v, u, p, d}` cells → HTML template where
every figure is `<a class="cell" href=url>` with a hover showing document + page
→ rewrite viewer host → run C and render flags → add ✓ anchoring badges from D
→ publish. `examples/meridian/` is the complete reference implementation
(`meridian_data.py` → `build_meridian.py` + `template_meridian.html`); copy it
and change the field selection for the deal type at hand.

**F. Integrity check.** `POST /v2/dataroom/file-veracity/initiate` with a
`fileId` → poll `…/status/{jobId}` until it resolves → report each check.

**G. Read a document.** Download to the shell's scratch area, extract what's
needed (text, a table, a figure), delete the file, cite page numbers.

**H. Workflow review.** List workflows → tasks → `get task` for detail → post a
comment (`parentId` to reply). Advance status one allowed hop at a time.

## 8. Handling rules

- Production is confidential: no holder names, no sharing outside Inveniam;
  pages built from it are internal. Sales is demo data and shareable.
- Every figure from extracted data links to its field. Every document listed
  links to the viewer.
- Statement data gets recipe C before it's shown; failures are flagged, not hidden.
- Preview-and-confirm before any destructive or permission call.
- Say what you couldn't verify. Viewer hosts, deal images (`slsus01-cdn`) and
  block explorers aren't reachable from here — the user checks those in a browser.

## 9. Worked example: The Meridian (sales)

Deal `26ca3be5-ac61-4d1e-900d-6605ad22fb1f`, real-estate, Chicago Class A office
tower: 30 documents / 8 folders / 24 with artifacts / 4,293 fields / 3,201 with
links; 30 of 30 anchored (62 ledger records; appraisals on 7 chains). Dashboard:
814 field links, 3 extraction flags (Q4 2025 balance-sheet Summary pulled from
the wrong month), ✓ badges per document. Published as *The Meridian Deal Room*
(Ryder's artifact). It exists to show recipes C, D and E working end to end —
nothing about it is specific to the toolkit.

Other sales deals for practice: Madison Ave Office, Main St Apartments
(real-estate); Mount Fuji XV LP, Mount Kita XV, Fund II, Fund 1, Lake Geneva XV,
Inveniam Private Equity Fund IV (funds); Conagra, Walt Disney, Coca-Cola,
Private Credit Portfolio, Big Construction Group, Potbelly, Square, Akamai (debt).
