# Inveniam API playbook — for the assistant

Read this once setup (START-HERE.md) is complete, together with
`skill/inveniam/SKILL.md` (the platform skill: resource model, workflow rules,
provisioning quirks, tool-name mapping; maintained at
https://github.com/aberdellans/Agent_skill). It is your working reference
for anything involving the Inveniam platform: how to call the API, what comes
back, the quirks that waste calls, and step-by-step recipes for the things
people ask for. Last verified 2026-10-05. Canonical copy: https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/API-PLAYBOOK.md (repo https://github.com/rbot9896-stack/inveniam-ai-toolkit).

---

## 1. Making a call

All calls go through `inv.py` (or its wrapper `inv.sh`) in the connected folder (`~/mnt/inveniam` in
Cowork's shell). It exchanges key + token for a short-lived JWT, caches it ~50
minutes per environment, and adds the headers. You never see credential values.

```
cd ~/mnt/inveniam
python3 inv.py GET "/v2/deals?page=1&limit=100"           # production (.env)   (Windows: python inv.py …)
python3 inv.py --env sales GET "/v2/deals?page=1&limit=100"   # sales (.env.sales); INV_ENV=sales also works
python3 inv.py --env demo-ce GET "/v2/deals?limit=10"         # demo-ce (.env.demo-ce)
python3 inv.py POST "/v2/dataroom/file-veracity/initiate" -d '{"fileId":"…"}'   # -d implies JSON; -H "k: v" and -o FILE also supported
```

Under the hood: `GET /v2/api-keys/auth/token` with headers `x-api-key: <key>`
and `Authorization: <token>` → `{"token": <jwt>}`; every call then sends
`Authorization: Bearer <jwt>` and `x-api-key`.

| | Production | Sales / demo | Demo-CE |
|---|---|---|---|
| REST base | `https://api.inveniam.app` | `https://slsus01-api.inveniam.app` | `https://demo-ce-api.inveniam.app` |
| Viewer host to use in links | `icp.inveniam.io` (API says `icp-v1`) | `sales.inveniam.io` (API says `sales-v1`) | not confirmed yet |
| MCP connector | ask Ryder | `https://sales-api.inveniam.io/mcp` (connector only; host not allowlisted for direct calls) | none known |
| Content | real, confidential | 28 demo deals (verified 2026-10-05), shareable | 26 real-estate deals, all "Coming Soon" (verified 2026-10-01); client data — confidential, never shareable |
| Spec | `GET /v2/api/docs/swagger-ui-init.js` (~640 KB — grep it; `/v2/api/docs-json` is 403) | same path | same path |

Working rules:
- **Sequential calls only.** Parallel `inv.py` calls from one shell return empty bodies.
- **Page everything.** `limit` ≤ 100; responses are `{items, meta}` (`meta.totalPages`). A list that stops at exactly 100 items has more pages. Production `/v2/deals` at 100 is ~50K chars — filter before printing.
- **Page order is not stable** on large lists (seen on the artifacts list): the same item can come back on two pages while another is skipped. De-duplicate by id and fetch what is still missing one by one.
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
| **All extracted fields for a deal** | `GET /v2/dataroom/datalab-provider/{dealId}/artifacts?page=&limit=50` | fastest route, but on large deals it returns HTTP 500 at bigger pages, can fail outright (Private Credit Portfolio) and duplicates/skips across pages. Use pages of 50, de-duplicate on `sourceAttributes.documentid`, then fetch missing documents one by one. `tools/fetch_deal.py` does all of this |
| One document's extraction | `GET /v2/dataroom/datalab-provider/{dealId}/artifacts/{documentId}` | 1–20 s each; documents never extracted return nothing |
| **Anchoring / taxonomy** | `GET /v2/dataroom/taxonomies/{documentId}` | array, one record per ledger — see §5. ~0.2–1 s each |
| File by hash | `GET /v2/files/by-checksum?hash=<sha256>` | finds a file from a checksum shown in the UI's DLT panel |
| Integrity check | `POST /v2/dataroom/file-veracity/initiate` `{fileId|taxonomyId|artifactId}` → `GET /v2/dataroom/file-veracity/status/{jobId}` | async; checks existence, taxonomy consistency, ledger verification, extraction validity |
| Datalab config | `GET /v2/datalab/document-types` · `/extraction/templates` · `/extraction/fields` | which document types and fields the extractor knows. Writes exist (`POST`/`PUT`) — see §3b before using them |
| Mongo connector status | `GET /v2/datalab/{dealId}/mongo-connection-status` | org-level external Mongo *output* connector; 403 on a sales Manager key |
| Workflows | `GET /v2/deals/{dealId}/workflows`, `…/tasks`, `GET /v2/workflows/tasks/{taskId}`, status/RACI/comment endpoints | see §6 |
| Data-room writes | create deal, create folders, upload files — see §3b | **no move, rename or delete via API** — UI only. `update_deal` can't change price; description caps ~1,500 chars |

Viewer links: whole document `https://<viewer>/view-file/{documentId}?id={dealId}`;
a field adds `&prev=1;{page}&formId=…&recordId=…&fieldId=…`. Rewrite the host
(§1 table) — the API returns the old one. Viewer hosts aren't reachable from
your shells; only the user's browser can open them.

### 3b. Writing: new deal, folders, uploads, Data Lab

Verified on sales 2026-10-02 with a key whose token can create deals (Manager on
existing deals is not enough; an admin-level token was used).

- **Create a deal:** `POST /v2/deals` with `dealTypeId`, `parentId`,
  `parentTargetId`, `calendarId`, `title`, `description`, `image` (`""` is
  accepted), `weekdays`. Copy the shape from an existing deal's record. Returns
  **201 with an empty body** — list deals to get the new id.
- **A new deal has no data room** until someone connects a storage provider to
  it in the UI; until then folder calls answer "Room not found".
- **Folders:** `POST /v2/dataroom/deals/{dealId}/{storageProviderConfigId}/create-folders`
  with `{"names": [...]}`.
- **Upload:** `POST /v2/deals/{dealId}/folder/{folderId}/upload-file`, multipart
  with `file` and `fileName`, **plus the header
  `Content-Disposition: attachment; fileName=<name>`** (no quotes) — without it
  the call fails with HTTP 500 "reading 'trim'". Sequential, ~1 s per file. The
  documents list lags uploads by about a minute.
- **Extraction starts by itself.** The platform classifies each upload and
  extracts it through a queue (roughly 0.5–1.5 documents a minute). No API call
  assigns a document type or triggers extraction. Types with no automatic
  template (seen: compliance certificates, side letters, subscription
  agreements) land as "Not Defined / Failed" and need manual extraction in the
  viewer: send for extraction from the data-room row, then for each field
  double-click the field and **highlight the value in the document** (typing a
  value in leaves no location). The viewer takes at most 2,000 characters per
  selection/field.
- **Data Lab writes** (`PUT /v2/datalab/extraction/field`,
  `PUT /v2/datalab/document-types/{id}`, `PUT /v2/datalab/extraction/templates/{id}`):
  a document type that is in use cannot be changed (HTTP 400 "Document Type is
  in use"); **created fields cannot be deleted** (no API call); types with
  `organisationId: null` / `isCustom: false` are platform-wide system types —
  never modify them. To add fields, create a custom type + template and move
  documents to it. Ask the user before any Data Lab write.

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

Flatten to rows `{doc, docId, ctype, form, rec, field, value, page, box, bb, url, built}`
— `tools/fetch_deal.py` does this into `deals/<slug>/cells.json` and `.csv`.

- `box` = the field has a usable highlight. Some locations carry **blank-string
  coordinates** (`"Left": ""`): a page but no highlight. Count only numeric
  coordinates. `bb` holds `[page, left, top, width, height]` per location
  (fractions of the page). Coverage varies a lot: Halcyon Ridge 99.7%, Meridian
  98%, Madison Ave 16%.
- **Values set by hand** in an automatically extracted record come back without
  `fieldPreviewURL`. Build the link from the ids in the platform's own format
  (`…/view-file/{doc}?id={deal}&prev=…&formId=…&recordId=…&fieldId=…`);
  `fetch_deal.py` does this and marks the row `built: true`.
- **Field and table names drift** between documents of the same type (an
  appraisal cap rate is `Value Cap Rate` in two quarters and `OCR Current
  Quarter` in the other two; investor/fund tables of a capital account
  statement swap names between quarters). Select by field name across
  aliases, and check the value before citing a field as the source.
Content types seen: APPRAISAL, INCOME_STATEMENT, BALANCE_SHEET, RENT_ROLL,
LEASE, CREDIT_AGREEMENT. Not every document has an artifact (decks, memos, cap
tables, ESA/title/zoning reports usually don't).

**Extraction can be wrong while looking right.** Example: a balance sheet's
Summary form took its totals from the January column instead of December. Before
relying on statement data, run the consistency checks in recipe C and tell the
user about any failure.

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

Which ledgers a deal anchors to is set per deal in the UI (data-room header,
"Connected validation services"); no public API call anchors a document or
changes a deal's ledgers. New uploads are anchored automatically on the
connected ledgers. Failed and long-pending records do occur (seen: Hedera
failed, NVNM/Mantra pending) — report them, don't hide them.

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
- Fund / private credit: NAV = fair value of investments + cash; LP capital
  accounts sum to NAV; capital called = loans funded + fees/organisational
  costs; schedule-of-investments principal = borrower balance-sheet debt =
  compliance-certificate debt; certificate ratios recomputed from that
  quarter's statements against the credit agreement's covenant levels; fund
  interest income = borrower interest expense.
- Units and scale: check the extracted `Units` against the PDF (seen: "In
  Actuals" extracted where the statement says thousands).
Report every failure with both values and their field links; don't silently
pick one.

**D. Anchoring audit.** Taxonomy call per document (sequential) → table of
document / ledgers Succeed / Pending / checksum. `fetch_deal.py` already saves
this as `anchoring.json`; `deal_summary.py` prints it.

**E. Integrity check.** `POST /v2/dataroom/file-veracity/initiate` with a
`fileId` → poll `…/status/{jobId}` until it resolves → report each check.

**F. Read a document.** Download to the shell's scratch area, extract what's
needed (text, a table, a figure), delete the file, cite page numbers.

**G. Workflow review.** List workflows → tasks → `get task` for detail → post a
comment (`parentId` to reply). Advance status one allowed hop at a time.

## 8. Handling rules

- Production and demo-ce are confidential: no holder names, no sharing outside
  Inveniam; anything built from them is internal. Sales is demo data and shareable.
- When you quote a number from extracted data, give its field link (recipe B).
- Statement data gets recipe C before it's relied on; failures are reported, not hidden.
- Preview-and-confirm before any destructive or permission call.
- Say what you couldn't verify. Viewer hosts, deal images (`slsus01-cdn`) and
  block explorers aren't reachable from here — the user checks those in a browser.

## 9. Deals in sales worth knowing

- **The Meridian** (`26ca3be5-ac61-4d1e-900d-6605ad22fb1f`), real-estate,
  Chicago Class A office tower: 30 documents / 24 extracted / 4,293 fields;
  30 of 30 anchored (62 ledger records, appraisals on 7 chains). The quickest
  first pull (about a minute). Its Q4 2025 balance-sheet Summary form took
  totals from the January column — a good test of recipe C.
- **Halcyon Ridge Direct Lending Fund I** (`0d5bde56-4820-4c20-a041-44ddc3f3e232`),
  fabricated private-credit fund, status Coming Soon: ~160 documents over 8
  quarters (LPA, capital calls, distributions, schedules of investments,
  capital account statements, six credit agreements + a waiver, 48 borrower
  statements, 48 compliance certificates). Everything reconciles across
  documents except two planted errors, and one borrower breaches a covenant.
  The best deal for fund/credit checks (recipe C) and for testing paging: the
  artifacts list duplicates and skips on it.
- **Private Credit Portfolio** (`453deb84-bc65-4a71-9ab6-3efd7a2c1b65`): 49
  real credit agreements from SEC filings plus compliance certificates and
  statements for one borrower. Its deal-level artifacts list fails; per
  document works. Total Commitment is blank on 21 agreements and 16 of 17
  certificates have no values.
- Others: Madison Ave Office, Main St Apartments, ten further real-estate deals
  (Brickworks, Cedar Hill, Seaport Row, …); Mount Fuji XV LP, Mount Kita XV,
  Fund II, Fund 1, Lake Geneva XV, Inveniam Private Equity Fund IV (funds);
  Conagra, Walt Disney, Coca-Cola, Big Construction Group, Potbelly, Square,
  Akamai (debt).
