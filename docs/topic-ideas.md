# Other buildathon topic ideas

Ideas in the same spirit as Call2Proposal: a real business workflow with an evidence trail and a human gate, not a one-prompt demo.

1. **Invoice chaser with receipts.** Reads unpaid invoices from an export, matches each to the email thread and PO quote it came from, drafts the follow-up in the customer's tone history, and holds every draft for approval. Guard: never states an amount that is not in the source invoice.
2. **Support-ticket to changelog.** Turns the week's closed tickets into a customer-facing changelog draft. Every changelog line links to the ticket it came from; anything the model generalizes beyond a single ticket is flagged for review.
3. **Hiring-loop debrief brief.** Combines interviewer scorecards into one debrief summary with verbatim quotes per competency. Conflicting ratings surface as conflicts instead of being averaged away; no hire/no-hire recommendation is generated - that stays with the panel.
4. **Vendor renewal radar.** Reads contract PDFs, extracts renewal dates, notice windows and price-escalation clauses with page-level citations, and drafts the renewal or cancellation note 60 days out. The escalation math is recomputed in code, never by the model.
5. **Founder sales-call CRM sync.** After each call, proposes CRM field updates (stage, amount, close date) as a diff against the current record. Nothing writes back without approval; every proposed change carries the transcript line that justifies it.

Each follows the same pattern: deterministic extraction with citations, retrieval for wording, a model only for prose, a verifier that voids unsupported claims, and a human gate before anything leaves the building.
