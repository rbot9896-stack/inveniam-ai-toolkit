# Instructions for the assistant working in this folder

This is the Inveniam AI Toolkit. If the user asks to be set up, onboarded, or
says anything like "set me up", "get started", "walk me through this":

1. Read `START-HERE.md` in this folder and follow it exactly — it is written
   for you. Begin at §0, then the intake in §1, one question at a time.
2. Never ask for, print, echo or store Inveniam API keys or tokens. They go
   into `.env` / `.env.sales` / `.env.demo-ce` here via the terminal snippet in §4 only.
3. Once setup is complete, read `API-PLAYBOOK.md` and `skill/inveniam/SKILL.md`;
   from then on those are your reference for anything Inveniam-related.

For any other Inveniam task in this folder (pull a deal, check anchoring, build
a dashboard, answer a question about a data room), read `API-PLAYBOOK.md`
first, then use `inv.py` / `tools/` as it describes.

Standing rules: production and demo-ce content (client data) are confidential and
never shareable; sales content is demo data. Every figure shown from extracted data links to its field
in the viewer (host rewritten). Run the consistency checks in the playbook
before presenting statement data and flag failures. Sequential API calls only.
Keep replies short; ask before building anything large.
