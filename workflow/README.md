# Workflow rebuild: sales call -> grounded proposal (no server)

Round-2 build for the Crework AI Engineer assignment. Round 1 (the app in this
repo's root) was declined for being a full hosted application. This folder is
the corrected shape: ONE Google Apps Script wired on top of Drive, Docs,
Sheets, Gmail and the Gemini API. Nothing deployed, no UI, no server.

## What it does
1. A `.txt` sales-call transcript lands in a Drive folder ("Calls In").
2. A 15-minute trigger picks it up and reads the "Past Proposals" folder.
3. Gemini 3.8 Flash (released Sept 2, 2026) extracts client facts, each with a
   verbatim quote from the call.
4. A deterministic pass checks every quote really is a substring of the
   transcript. Failed facts are dropped before drafting.
5. Gemini drafts the proposal from verified facts only; anything the call
   never stated becomes a `[CONFIRM: ...]` placeholder, never an invention.
6. A second deterministic pass flags every dollar amount that does not appear
   in the transcript or a past proposal.
7. Output: a Google Doc (proposal + verification report) in "Proposals Out",
   a row in the tracker Sheet, and a Gmail DRAFT for the founder to review.
   Nothing sends itself - the human send is the approval gate.

## Setup
Copy `Code.gs` into script.google.com, fill the six CONFIG constants
(API key, three folder IDs, sheet ID, your email), run `installTrigger` once.
