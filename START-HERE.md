# Inveniam AI Toolkit — guided setup

**What this is.** Everything needed for an AI assistant (Claude or ChatGPT) to
work fluently with the Inveniam platform through its API: read deals and data
rooms, pull every extracted field with a link to its source, verify on-chain
anchoring, run integrity checks, drive workflows, and build pages where every
number clicks through to the document it came from. One deal (The Meridian, in
the sales environment) is included as a worked example; the point is the
capability, not that deal.

**How to use it.** In a new conversation with Claude or ChatGPT, paste:

> Read https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/START-HERE.md and walk me through the setup.

(or paste this file's contents, or attach the toolkit folder). The assistant
asks a few questions and takes you through it one step at a time. You do two
things yourself: create API credentials on the Inveniam website and paste them
into a terminal window once. Nothing sensitive goes into the chat.

**Use Cowork or Codex, not the chat window.** Start this in the Claude desktop
app's **Cowork** tab, or in the ChatGPT desktop app with the top picker set to
**Codex**. Those can open the toolkit folder and run things for you; the chat
websites — and the desktop apps in plain chat mode — cannot, and the assistant
will ask you to restart in the right place (§0 explains how).

Repository: https://github.com/rbot9896-stack/inveniam-ai-toolkit (public, no
credentials inside — updates land here, so prefer it over an emailed zip).
Maintained platform skill: https://github.com/aberdellans/Agent_skill

Prepared by Ryder Desenberg (Inveniam), 2026-09-24.

---

## §0. Before anything else: are we in the right place?

**This matters more than any other step.** Both Claude and ChatGPT have a plain
chat window and a separate "works on your computer" mode. The chat window
cannot open folders or run commands, so the setup dead-ends there. The
assistant must establish which one it is running in **as its very first
action**, before the intake in §1, and move the user if needed.

| | Plain chat — wrong place for setup | Working mode — right place |
|---|---|---|
| Claude | claude.ai in a browser; or the desktop app's **Chat** tab | Desktop app → **Cowork** tab (left sidebar) → *New task* → **Link to this computer** |
| ChatGPT | chatgpt.com in a browser; or the desktop app with the top picker on **ChatGPT** | Desktop app → picker at the top of the window → **Codex** → open a folder as the project |

**How the assistant tells:** try to list a folder or run `echo ok`. If you
cannot run anything on the user's computer, you are in plain chat.

**If in plain chat, say this and stop** (don't start the intake; don't have
them create API keys yet — it would only be redone):

> This setup needs the version of me that can work on your computer, and this
> chat window can't. Let's restart in the right place — it takes a minute and
> nothing is lost.
>
> **Claude:** open the Claude desktop app (https://claude.ai/download if you
> don't have it). In the left sidebar click **Cowork**, then **New task**, then
> **Link to this computer**. In that task, paste the same message you sent me.
>
> **ChatGPT:** open the ChatGPT desktop app (https://chatgpt.com/download). At
> the top of the window there's a picker that says **ChatGPT** — switch it to
> **Codex**. When it asks for a project or folder, pick or create
> `dev/inveniam` in your home folder. Then paste the same message you sent me.
>
> If you only want to *ask questions* about deals and don't need documents,
> extracted data or dashboards, stay here — that's §5, and it works in chat.

The one thing plain chat *can* do is §5 (the connector). If the user is in
chat and asks only for that, do §5 and nothing else.

---

## Instructions for the assistant

You are guiding someone who may not be technical. For the whole conversation:

0. **First, §0.** Confirm you are running in Cowork or Codex (you can run a
   command on the user's computer). If not, give the §0 restart message and
   stop. Re-check whenever the user says they've switched.
1. **One step at a time.** One question or one instruction, then wait. Never
   paste the whole guide at them.
2. **Confirm before advancing.** After each step, ask what they see and check
   it against the expected result written in that step. If it doesn't match,
   troubleshoot with §7 before continuing.
3. **Adapt.** Run the intake in §1 first; then take only the branches that apply
   (Mac/Windows, Claude/ChatGPT, which environments, admin or member).
4. **Never ask for, print, or store API keys or tokens.** They go into a file on
   the user's computer through the terminal snippet in §4. If a key lands in
   the chat by mistake, tell them to regenerate it in Inveniam and don't repeat
   it.
5. **Do the work yourself when you can.** As Claude in Cowork linked to their
   computer you can create folders, copy files and run commands — do that rather
   than dictating. Otherwise give the exact command to paste and ask what came
   back.
6. **When setup is complete, read `API-PLAYBOOK.md` and `skill/inveniam/SKILL.md`** in the toolkit (or from https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/API-PLAYBOOK.md and https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/skill/inveniam/SKILL.md if you can't see the folder). It is
   written for you: how to call the API, what every endpoint returns, the
   quirks, and step-by-step recipes for the capabilities. From then on, that is
   your reference for anything Inveniam-related.
7. **Explain every terminal step — in the depth the user chose.** Before any
   Terminal or PowerShell snippet, say (a) what the terminal is, the first time:
   a plain text window where you type instructions to your own computer — the
   assistant never sees it; (b) what this snippet will do, in one or two plain
   sentences; (c) why it's needed. In **Guided** mode give all three every time,
   plus the "What this does" note printed under the snippet. In **Quick** mode
   give one line ("This creates the folder and downloads the toolkit into it.")
   and the snippet. In both modes, never skip (b) for the credentials snippet
   in §4 — the user is about to paste secrets and must know where they go. If
   they ask "why?" at any point, switch to the Guided depth for that step.
8. Keep replies short and plain.

---

## §1. Intake — one question at a time

1. *"Mac or Windows PC?"*
2. *"Which assistant are we in — Claude or ChatGPT?"* (You already know from
   §0 that you're in Cowork or Codex; if you're not, you shouldn't be here —
   go back to §0.)
3. *"Which Inveniam environments do you have a login for — sales
   (sales.inveniam.io), production (icp.inveniam.io), or both?"* Do sales first:
   demo data, safe to experiment on.
4. *"Are you an owner/admin of your Claude or ChatGPT workspace, or a member?"*
5. *"Do you want the conversational connector, the full API route, or both?"*
   Recommend both. One line each: the connector answers questions about deals
   inside a chat; the API route (desktop app: Claude Cowork or Codex) is what
   reads extracted data, downloads documents, checks anchoring and builds
   dashboards.
6. *"A few steps use the terminal — a text window where you paste a line and
   your computer runs it. Would you like me to explain what each one does
   before you run it (Guided), or just give you the lines (Quick)?"*
   Default to Guided if they're unsure. They can switch at any time.

Summarise the plan in three lines, then start.

---

## §2. Folders — the layout everything expects

| | Mac | Windows |
|---|---|---|
| Base | `~/dev/inveniam` | `%USERPROFILE%\dev\inveniam` |
| Helpers | `~/dev/inveniam/tools/` | `…\dev\inveniam\tools\` |
| Pulled deals | `~/dev/inveniam/deals/<deal-slug>/` (created automatically) | same |
| Worked example | `~/dev/inveniam/examples/meridian/` | same |
| Claude skill | `~/dev/inveniam/skill/inveniam/SKILL.md` (installed in §5b) | same |
| Credentials | `~/dev/inveniam/.env.sales`, `~/dev/inveniam/.env` | same names, same folder |

Pick **one** of the two ways below. Both end with the toolkit's files sitting
directly in the base folder (no extra folder in between).

**Option A — `git clone` (preferred: `git pull` later picks up updates).**

*What this does:* creates a `dev` folder in your home folder if it isn't there,
then asks `git` (a standard tool for copying code from the internet) to download
the toolkit from GitHub into `dev/inveniam`. Nothing else on your computer is
touched. *Why:* the helper scripts have to live on your machine, in a folder the
assistant can be pointed at, before they can run.

Mac — Terminal (Spotlight → "Terminal"). If it asks to install the command-line
developer tools, click *Install*, wait, then run the line again:
```zsh
mkdir -p ~/dev && git clone https://github.com/rbot9896-stack/inveniam-ai-toolkit.git ~/dev/inveniam && echo cloned
```
Windows — PowerShell (Start → "PowerShell"). Needs Git for Windows
(https://git-scm.com/download/win, defaults are fine; reopen PowerShell after):
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\dev" | Out-Null; git clone https://github.com/rbot9896-stack/inveniam-ai-toolkit.git "$env:USERPROFILE\dev\inveniam"; "cloned"
```
Expected: `cloned`. If it says the destination already exists and is not empty,
rename the old `inveniam` folder aside and run it again, or use Option B.

If you are Claude in Cowork with the computer linked, or Codex on the machine,
run the clone yourself,
then ask the user to **Add folder** → `dev/inveniam` so you can see it.

**Option B — Download ZIP (no git needed).**
1. Open https://github.com/rbot9896-stack/inveniam-ai-toolkit → green **Code**
   button → **Download ZIP**.
2. Unzip it. The folder is called `inveniam-ai-toolkit-main`.
3. Rename that folder to `inveniam` and move it into a `dev` folder in your home
   folder — Mac: `/Users/<you>/dev/inveniam`; Windows: `C:\Users\<you>\dev\inveniam`.
   Create `dev` if it isn't there.

**Check** — Mac: `ls ~/dev/inveniam ~/dev/inveniam/tools` · Windows:
`Get-ChildItem "$env:USERPROFILE\dev\inveniam" -Recurse -Name`
Expected: `inv.py`, `inv.sh`, `API-PLAYBOOK.md`, `START-HERE.md`, `README.md`,
a `tools` folder with `fetch_deal.py` and `deal_summary.py`, an `examples`
folder, a `skill` folder — and **no** `inveniam-ai-toolkit-main` folder nested inside.

**Updating later** — Option A: `cd ~/dev/inveniam && git pull`. Option B:
download again and replace the files. Your `.env` credential files are not in
the download and are left untouched either way.

Windows note: the helpers are plain Python (`inv.py`, `tools/fetch_deal.py`);
the `.sh` files are thin wrappers for Mac/Linux and can be ignored on Windows.
Inside Claude Cowork nothing is needed (its shell is Linux with Python). With
Codex on Windows, install Python once from the Microsoft Store ("Python 3.12"
or newer), then every command below works in PowerShell with `python` in place
of `python3`.

---

## §3. Create API credentials (the user does this, per environment)

| Environment | Log in at | Base URL for §4 |
|---|---|---|
| Sales / demo | https://sales.inveniam.io | `https://slsus01-api.inveniam.app` |
| Production | https://icp.inveniam.io | `https://api.inveniam.app` |

1. Log in → **Settings → Public API Keys → Create API key.** Name it
   `ai-<yourname>`.
2. Open the new key → **Generate token.** Choose a role that can read deals,
   data-room documents and data artifacts — *Manager* on the deals you care
   about is enough. Avoid Administrator unless nothing else is offered.
3. Leave key and token on screen for §4. **Don't paste them into this chat.**

Can't see Public API Keys? Their org role lacks the API-key permission (it's on
Administrator or a custom role, not default Manager) — an Inveniam admin grants
it or creates the pair for them.

Ask: *"Do you have a key and a token on screen?"* Proceed only on yes.

---

## §4. Write the credentials file (the user pastes one snippet)

*What this does:* the snippet asks you to paste the key, then the token; as you
paste, nothing appears on screen (that's deliberate). It then writes both into a
small hidden file called `.env.sales` inside `dev/inveniam`, makes that file
readable only by your user account, and prints the *length* of each value so
you can see it landed without showing it. *Why:* the assistant must never see
your credentials, so they go straight from your clipboard into a file on your
own disk, and the helper scripts read them from there. Say this in every mode
before giving the snippet.

**Mac — Terminal — sales:**
```zsh
read -rs "K?Inveniam SALES API key: "; echo
read -rs "T?Inveniam SALES API token: "; echo
umask 077
printf 'INVENIAM_API_KEY=%s\nINVENIAM_API_TOKEN=%s\nINVENIAM_BASE_URL=%s\n' \
  "$K" "$T" "https://slsus01-api.inveniam.app" > ~/dev/inveniam/.env.sales
unset K T; chmod 600 ~/dev/inveniam/.env.sales
awk -F= '{print $1, length($2)}' ~/dev/inveniam/.env.sales
```

**Windows — PowerShell — sales:**
```powershell
$K = Read-Host -AsSecureString "Inveniam SALES API key"
$T = Read-Host -AsSecureString "Inveniam SALES API token"
$k = [Runtime.InteropServices.Marshal]::PtrToStringUni([Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($K))
$t = [Runtime.InteropServices.Marshal]::PtrToStringUni([Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($T))
$f = "$env:USERPROFILE\dev\inveniam\.env.sales"
"INVENIAM_API_KEY=$k`nINVENIAM_API_TOKEN=$t`nINVENIAM_BASE_URL=https://slsus01-api.inveniam.app`n" | Set-Content -NoNewline -Encoding ascii $f
icacls $f /inheritance:r /grant:r "${env:USERNAME}:F" | Out-Null
Remove-Variable K,T,k,t
Get-Content $f | ForEach-Object { $p = $_ -split '=',2; "$($p[0]) $($p[1].Length)" }
```

**Production:** same snippet with `https://api.inveniam.app` and file name
`.env` (no suffix).

Expected: three lines, e.g. `INVENIAM_API_KEY 40 / INVENIAM_API_TOKEN 180 /
INVENIAM_BASE_URL 34` — all above 0.

---

## §5. Connector route (conversation inside Claude or ChatGPT)

Connector URLs: sales `https://sales-api.inveniam.io/mcp`; production — ask
Ryder (not public).

**First ask which plan they're on** — it decides who can add the connector.
Q4's owner/member answer only matters for the workspace plans.

**Claude — any plan, including Free.** A "custom connector" is Claude's name
for adding an MCP server; this is the only step that involves MCP. (The API
route in §6 doesn't use it at all.)

- *Free:* **tell the user first:** Free accounts get **one** custom connector in
  total. Adding Inveniam uses that slot; to add a different one later they'd
  have to remove Inveniam or upgrade. Proceed only if they're fine with that.
  Then the same steps as Pro/Max.
- *Pro / Max (personal):* the user does it themselves — *Customize →
  Connectors → + → Add custom connector → paste URL → Add → Connect.*
- *Team / Enterprise:* only an **Owner** can add it, once: *Organization
  settings → Connectors → Add → Custom → Web → paste URL → Add.* If the user is
  a member, give them exactly that sentence to forward — nothing more is needed
  from the owner. Then the user: *Customize → Connectors → Inveniam → Connect*
  (sign in with the Inveniam login). Per chat: *+ → Connectors → toggle on.*

**ChatGPT** — custom connectors need *Developer mode*, web app only
(chatgpt.com, not the mobile app).

- *Free / Go:* not available. Options: upgrade to Plus, use Claude Free for
  the connector, or skip straight to §6 — Codex is included on Free and gives
  them the API route, which is the more capable one anyway.
- *Plus / Pro (personal):* the user does it themselves — *Settings → Apps* (or
  *Connectors*) *→ Advanced settings → Developer mode on*; if the toggle isn't
  there, look under *Settings → Security*. Then *Apps → Create*: name, server
  URL, authentication as requested, **Scan tools**.
- *Business:* a workspace **Owner** turns on Developer mode once (*Workspace
  settings → Permissions & Roles → Connected Data → Developer mode*). Ask for
  only that. Then the user creates the app under *Settings → Apps → Create* as
  above.
- *Enterprise / Edu:* an admin enables Developer mode as above and usually
  also creates and publishes the app workspace-wide (*Workspace settings →
  Apps → Create → Scan tools → publish*). Give them the URL and the name
  *Inveniam Sales*.

In a chat, select or @mention the app on the message that needs it.

Tell users plainly: the connector answers questions only. Documents,
extracted fields, anchoring and dashboards come from §6, which needs a desktop
app (Claude or Codex).

Test: *"List the deals in the Inveniam sales environment."* Expected: 17
deals, including The Meridian, Madison Ave Office, Coca-Cola, Fund II.

### §5b. Install the Inveniam skill (Claude only — do this for everyone on Claude)

The platform skill's home is **https://github.com/aberdellans/Agent_skill**
(folder `inveniam/`); a copy is bundled here as `skill/inveniam/SKILL.md`. Use
the GitHub version when in doubt — it is the maintained one. That README also
has per-platform install steps (Claude.ai, Claude Code, Codex, ChatGPT).

The skill: it teaches Claude the resource
model, the workflow status rules, the `deal-id` header quirk, data-room write
limits and the preview-and-confirm rule, and — because of its description —
makes Claude recognise Inveniam tasks even when the platform isn't named.

- **Claude Cowork / desktop:** in a Cowork task with the toolkit folder
  connected, say *"Add the skill in skill/inveniam/SKILL.md to my skills."*
  Claude proposes it and the user clicks Save on the review card.
- **Claude web (Team/Enterprise):** an admin can add it under *Organization
  settings → Skills*; individuals under *Customize → Skills → Add*, uploading
  `SKILL.md`. If the Skills menu isn't present on the plan, add the file to the
  project's knowledge instead (§5c).
- **ChatGPT:** follow the ChatGPT install steps in the repo README, or paste the
  file into a Custom GPT's instructions / a project's knowledge (§5c).

### §5c. Optional — a project for the whole team

Create a Claude Project (or ChatGPT project) named *Inveniam API*, upload
`API-PLAYBOOK.md`, `START-HERE.md` and `skill/inveniam/SKILL.md` to its
knowledge, and paste this as its instructions:

> Read API-PLAYBOOK.md before doing anything against the Inveniam platform.
> Reach the API through ~/dev/inveniam/inv.py on the user's computer (request
> access to that folder if it isn't connected); don't rely on the connector.
> Never ask for, print or copy API keys or tokens. Production content is
> confidential and never shareable; sales content is demo data. Every figure
> shown from extracted data must link to its field in the viewer, host
> rewritten. Run the consistency checks in the playbook before presenting
> statement data and flag anything that fails on the page. Keep responses
> terse; ask before building something large.

Every conversation started in that project then has the playbook and skill
loaded.

Say the limits plainly: the connector can't download documents or read
extracted fields, and the production one has been flaky. It's for questions.

---

## §6. API route (an assistant running on the user's computer)

This route needs an assistant that can run the helper scripts on the user's
machine. Two qualify, and the toolkit works identically with either:

| | Claude | ChatGPT |
|---|---|---|
| Tool | **Claude desktop app** (Cowork) | **ChatGPT desktop app, switched to Codex mode** (or Codex CLI) |
| Plans | Pro, Max, Team, Enterprise (not Free) | every plan, including Free and Go (small allowance on Free) |
| Get it | https://claude.ai/download | ChatGPT desktop app from https://chatgpt.com/download; Codex is the second entry in the mode picker at the top of the window (ChatGPT / **Codex**) · CLI: `npm i -g @openai/codex` |
| Windows | works as-is (Cowork's shell is Linux) | works natively — needs **Python** (Microsoft Store → "Python 3", one click); no WSL |

**Recommend the desktop app on both sides** — the chat website can't run
anything on the computer, and the desktop apps are the comfortable way in for
a non-technical user (link the computer, pick a folder, talk). If someone is on
Claude Free and wants this route, Codex with their ChatGPT login is the free
way to get it.

**Using both Claude and Codex?** Nothing extra to do. Both open the same
folder (`~/dev/inveniam`), and `inv.py` reads the `.env` files that sit beside
it — so the credentials from §4 are written once and shared. Don't make a second
copy of the folder or the `.env` files per assistant; that's how they drift.

Here the assistant runs the commands, not the user. In Guided mode, still say
what each one does before running it: 2 checks the Inveniam API can be reached
from this computer (on Windows/PowerShell use `curl.exe`, not `curl`); 3 proves the credentials file works by asking for one deal;
4 downloads one deal's inventory and extracted data into `deals/`; 5 builds the
example dashboard page from that data.

1. Open the folder in the assistant.
   - *Claude:* desktop app → new Cowork task → **Link to this computer** →
     **Add folder** → `dev/inveniam`. In Claude's shell it appears as
     `~/mnt/inveniam` (Mac and Windows alike); use that path below.
   - *Codex:* ChatGPT desktop app → mode picker at the top → **Codex** (not
     ChatGPT — that mode can't run anything on the computer) → open
     `dev/inveniam` as the project (CLI: `cd ~/dev/inveniam && codex`); it uses
     the ChatGPT login already in the app.
     The path is the real one, `~/dev/inveniam`; use that below. Approve each
     command when Codex asks.
2. Reachability (assistant runs):
   `curl -s -o /dev/null -w "%{http_code}\n" -m 15 https://slsus01-api.inveniam.app/v2/api/docs/`
   → `200`. If `000` in Claude on a Team/Enterprise plan, the org's allowlist
   blocks it: an admin adds `slsus01-api.inveniam.app` and `api.inveniam.app`
   under *Claude Organization settings → Capabilities → allowed domains*. (This
   "Capabilities" setting is a network allowlist — nothing to do with the MCP
   connector in §5.) In Codex, `000` means the machine itself can't reach the
   host — check the network.
3. Credentials (assistant runs, from the folder):
   `python3 inv.py --env sales GET "/v2/deals?limit=1"` (Windows: `python inv.py …`)
   → JSON with `"items"` and `"meta"`. `401` → back to §3 step 2.
   `No credentials file` → §4 landed in the wrong place.
4. First real pull (assistant runs):
   ```
   python3 tools/fetch_deal.py --env sales "The Meridian"
   python3 tools/deal_summary.py deals/the-meridian
   ```
   → after the pull: `The Meridian: 30 documents, 8 folders, 24 artifacts, 4293
   cells, 3201 with viewer links` and `30 documents with anchoring records`;
   then a Markdown table of 30 documents with field counts and ✓ anchoring
   ledgers. Try another deal by title to show it's generic:
   `python3 tools/fetch_deal.py --env sales "Madison"`.
5. Optional — the worked dashboard example:
   ```
   python3 examples/meridian/meridian_data.py && python3 examples/meridian/build_meridian.py
   ```
   → `examples/meridian/meridian.html`. Claude publishes it as an artifact;
   Codex opens it in the browser (`open examples/meridian/meridian.html` on
   Mac). Expected on the page: KPIs $208,300,000 · 6.00% · $694.33 ·
   $11,950,796 · 91.7% · $70,000,000; three amber `!` flags on the Q4 2025
   balance sheet; green ✓ on all 30 documents. Clicking any figure opens that
   field in sales.inveniam.io (log in there once).
6. **Now read `API-PLAYBOOK.md`** and tell the user setup is complete and what
   they can ask for (§8 has examples).

---

## §7. Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `000` from the curl check | Network allowlist → admin adds the host (§6.2) |
| `401` from `inv.py` | No token for the key, or wrong role → §3 |
| `permissionsError` | Token's role can't see that resource → higher role on the deal |
| `No credentials file` | Wrong folder or name → `.env.sales` directly in the base folder |
| Empty response / 0-byte file | Intermittent API behaviour → rerun; never run calls in parallel |
| `spawn E2BIG` in Cowork | Command too long → Claude writes a script file and runs it |
| Field link opens a login page | Expected → log in to that environment's viewer once |
| Connector shows no tools / drops | Known flakiness → use §6 for anything that matters |
| No Public API Keys menu | Org role lacks the permission → Inveniam admin |

---

## §8. What people can ask for once this is done

- *"List the deals in sales / production."*
- *"Pull `<deal>` and give me the data-room inventory with anchoring status."*
- *"Which documents in `<deal>` are anchored on which chains? Show the transaction ids."*
- *"Pull the extracted fields from `<document>` and show each one with its page link."*
- *"Build a dashboard for `<deal>` where every figure links to its source."*
- *"Check `<statement>` against its own detail table and flag inconsistencies."*
- *"Run an integrity (veracity) check on `<document>`."*
- *"Show the workflow tasks on `<deal>` and who's responsible."*
- *"Download `<document>`, extract X, then delete the copy."*

Standing rules the assistant follows: credentials never leave the `.env` files;
every figure shown from extracted data links to its field in the viewer;
production content stays internal, sales content is shareable; statement data
is arithmetic- and cross-checked before it's presented, with failures flagged
on the page; destructive or permission-changing API calls are previewed and
approved first.

Owner: Ryder Desenberg — helpers, production MCP URL, and the Claude project
*Inveniam API* with the full technical notes.
