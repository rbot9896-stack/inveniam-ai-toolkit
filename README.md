# Inveniam AI Toolkit

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

No credentials are in this repository. They live only in `.env` files on each
user's own computer, created during setup.

Environments: production `api.inveniam.app` (confidential), sales
`slsus01-api.inveniam.app` (demo data). Maintainer: Ryder Desenberg.
