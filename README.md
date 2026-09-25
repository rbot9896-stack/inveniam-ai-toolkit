# Inveniam AI Toolkit

**Quick start:** open Claude or ChatGPT and paste:

> Read https://raw.githubusercontent.com/rbot9896-stack/inveniam-ai-toolkit/main/START-HERE.md and walk me through the setup.

Works with the Claude desktop app (Cowork) or OpenAI Codex — both can run the
helpers on your machine and share the same credentials folder.

Everything an AI assistant (Claude or ChatGPT) needs to work fluently with the
Inveniam platform through its API: setup for every environment, a playbook of
endpoints and recipes, helper scripts, the platform skill, and one worked example.

| Start with | Who it's for |
|---|---|
| `START-HERE.md` | anyone setting up — paste it into Claude or ChatGPT and say "walk me through this" |
| `API-PLAYBOOK.md` | the assistant, after setup — how to call the API, what comes back, recipes |
| `skill/inveniam/SKILL.md` | the platform skill (maintained at https://github.com/aberdellans/Agent_skill) |
| `inv.sh`, `tools/` | API helper; pull any deal, summarise inventory / extraction / anchoring |
| `examples/meridian/` | worked example: a provenance dashboard where every figure links to its source field |

Get the files — either:
- `git clone https://github.com/rbot9896-stack/inveniam-ai-toolkit.git ~/dev/inveniam` (then `git pull` for updates), or
- green **Code → Download ZIP**, unzip, rename the folder to `inveniam` and put it in `~/dev`.

Either way the files must sit directly in `~/dev/inveniam` (`inv.sh`, `tools/`, …); `START-HERE.md` §2 walks through it.

No credentials are in this repository. They live only in `.env` files on each
user's own computer, created during setup.

Environments: production `api.inveniam.app` (confidential), sales
`slsus01-api.inveniam.app` (demo data). Maintainer: Ryder Desenberg.
