---
name: answer-questionnaire
description: Write cited answers straight into a governance questionnaire's answer cells and list the open questions per lead
code: AQ
added: 2026-09-26
type: prompt
---

# Answer a Questionnaire

Run only when your owner names a questionnaire and asks you to answer it, in full or for named questions.

## What success looks like

Every answer cell in the questionnaire .docx holds a concise answer ending with the reasoning note, written directly (owner's standing rule: no review-file drafts for answers). An answer the files can't support is written as `OPEN — <lead> to provide.` with one line of context, so the owning lead sees exactly what you need from them. Every draft stands on evidence named in its reasoning note: a BMad artifact and its section or decision id, or an official Microsoft URL. Where the evidence runs out, the draft says so plainly and the item waits for its lead. The leads will sign these answers into a governance record, so a clean gap is always better than a plausible sentence.

Hand back a short list per lead of the items that need them, the most consequential first, each phrased so the lead can answer it in a line or two.

## What you must hold

- Classify each question by owner and by source tier (your CREED's source order). Business impact, revenue, users, core processes, RTO and RPO, adjoining systems, partners and vendors belong to the Product Lead; platform, stack and security controls to the Tech Lead. A question that spans both goes to the lead who must sign it, with the other named in the source line.
- Consult the answer library (AL) for how past projects answered the same question, and mention a match in the note as reference only. Never lift a figure from it. RTO and RPO are always asked fresh.
- A .docx answer cell that already holds text is an existing answer: verify it against the artifacts and draft either a confirmation or a correction, citing what you checked.
- Prefer safe-docx (tracked changes) when its tools are loaded; otherwise python-docx writes the answer cells directly.
- Read the .docx with the safe-docx MCP server when it is available; otherwise python-docx (`uv run --with python-docx python …`) reads the question table.
- Before handing back, re-read the answer cells and confirm every answer ends with the reasoning note.
