---
name: answer-questionnaire
description: Write cited answers straight into a governance questionnaire's answer cells and list the open questions per lead
code: AQ
added: 2026-09-26
type: prompt
---

# Answer a Questionnaire

Run only when your owner names a questionnaire and asks you to answer it, in full or for named questions. One questionnaire per session (SKILL.md): if you've already finished one this session, say so and suggest picking the next one up fresh rather than starting it now.

## What success looks like

Every answer cell in the questionnaire .docx holds a concise answer ending with the reasoning note, written directly (owner's standing rule: no review-file drafts for answers). An answer the files can't support is written as `OPEN — <lead> to provide.` with one line of context, so the owning lead sees exactly what you need from them. Every draft stands on evidence named in its reasoning note: a BMad artifact and its section or decision id, a dated clause of one of the region's regulatory sources, or an official Microsoft URL. Where the evidence runs out, the draft says so plainly and the item waits for its lead. The leads will sign these answers into a governance record, so a clean gap is always better than a plausible sentence.

Hand back a short list per lead of the items that need them, the most consequential first, each phrased so the lead can answer it in a line or two.

## What you must hold

- Extract the question table with `uv run scripts/questionnaire.py extract <docx>`: id, question, current answer and a content hash per row, with no need to open the document any other way. Never read a questionnaire .docx by any other means.
- Re-answer only a row that needs it: this project's answer library (AL) has no hash on file for it yet (first pass), its hash differs from the one AL recorded last time, it carries an open reviewer comment (`docx-comments.py`), or drift-check (DR) has an open `D-<n>` against it. Every other row keeps its recorded answer untouched — don't re-derive, re-cite or re-check it. Say in one line how many rows you skipped this way.
- Classify each row you do answer by owner and by source tier (your CREED's source order). Business impact, revenue, users, core processes, RTO and RPO, adjoining systems, partners and vendors belong to the Product Lead; platform, stack and security controls to the Tech Lead. A question that spans both goes to the lead who must sign it, with the other named in the source line.
- When the region has sources, check each row you answer against their `applies_to`. A question a source governs gets the clause it relies on, with the regulator's requirement kept apart from what the project's artifacts commit to (CREED source order and Regulatory source dates).
- A Cloud Assessment answer may also cite the project's architecture diagram (from `leonardo-da-vinci`, in the `org` config's `diagrams_folder`) beside the AD it was drawn from, never instead of it, and only when `uv run ../leonardo-da-vinci/scripts/diagram-drift.py {project-root}` reports that diagram `current` or `outdated`; a `stale` one gets its drift named to your owner instead.
- Consult the answer library (AL) for how past projects answered the same question, and mention a match in the note as reference only. Never lift a figure from it. RTO and RPO are always asked fresh.
- When a row due for re-answering already holds text, that's an existing answer, not a blank: verify it against the artifacts and draft either a confirmation or a correction, citing what you checked.
- Prefer safe-docx (tracked changes) when its tools are loaded; otherwise `uv run scripts/questionnaire.py write <docx> <answers.json>` writes the answer cells directly, from one JSON file mapping row id to finished answer text (reasoning note included). Either way, only the answer cell's text changes — the org's table structure, columns and formatting stay exactly as issued.
- After writing, record each answered row's question and hash alongside its answer in the answer library (AL), so the next pass can compare hashes instead of rereading the question.
