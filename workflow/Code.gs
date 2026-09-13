// ============================================================================
// CALL-TO-PROPOSAL WORKFLOW
// A sales-call transcript lands in a Drive folder. This script turns it into
// a grounded proposal Doc, logs it to a Sheet tracker, and parks a review
// draft in Gmail. Nothing sends itself - a human approves every proposal.
//
// Stack: Google Drive + Docs + Sheets + Gmail + Gemini API. One file,
// nothing deployed, no server, no UI.
// ============================================================================

// ---- CONFIG: fill these in -------------------------------------------------
const GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY";
const CALLS_FOLDER_ID = "PASTE_CALLS_IN_FOLDER_ID";
const PAST_PROPOSALS_FOLDER_ID = "PASTE_PAST_PROPOSALS_FOLDER_ID";
const OUT_FOLDER_ID = "PASTE_PROPOSALS_OUT_FOLDER_ID";
const SHEET_ID = "PASTE_TRACKER_SHEET_ID";
const FOUNDER_EMAIL = "PASTE_YOUR_EMAIL";

const MODEL = "gemini-3.8-flash"; // shipped Sept 2, 2026 - the new capability
const SHEET_TAB = "Pipeline";
// ----------------------------------------------------------------------------

// Entry point: run manually, or on the 15-minute trigger from installTrigger().
function processNewTranscripts() {
  const callsFolder = DriveApp.getFolderById(CALLS_FOLDER_ID);
  const processedFolder = getOrCreateSubfolder_(callsFolder, "Processed");
  const pastProposals = readFolderTexts_(DriveApp.getFolderById(PAST_PROPOSALS_FOLDER_ID));

  const files = callsFolder.getFiles();
  while (files.hasNext()) {
    const file = files.next();
    if (!/\.txt$/i.test(file.getName())) continue; // transcripts arrive as .txt
    const transcript = file.getBlob().getDataAsString();
    processOneTranscript_(file, transcript, pastProposals, processedFolder);
  }
}

function processOneTranscript_(file, transcript, pastProposals, processedFolder) {
  const startedAt = new Date();
  let status = "Proposal Ready";
  let notes = "";

  // STEP 1 - EXTRACT. Every fact must carry a verbatim quote from the call.
  const facts = extractFacts_(transcript);

  // STEP 2 - VERIFY (deterministic, no model): each quote must be a real
  // substring of the transcript. A quote the model paraphrased or invented
  // fails here, and the fact it supports gets thrown out before drafting.
  const audit = auditQuotes_(facts, transcript);
  const dropped = audit.filter(a => !a.ok);
  if (dropped.length > 0) {
    status = "Needs Review";
    notes = dropped.length + " fact(s) failed quote check: " +
      dropped.map(d => d.field).join(", ");
  }

  // STEP 3 - DRAFT. Only audited facts go in. Anything the call never stated
  // becomes a [CONFIRM] placeholder - the model is told not to invent it.
  const proposalText = draftProposal_(audit.filter(a => a.ok), pastProposals);

  // STEP 4 - CLAIM AUDIT (deterministic): every dollar amount in the draft
  // must trace back to the transcript or a past proposal. Untraceable numbers
  // are flagged in the verification report, not silently shipped.
  const moneyFlags = auditMoneyClaims_(proposalText, transcript, pastProposals);
  if (moneyFlags.length > 0) {
    status = "Needs Review";
    notes = (notes ? notes + "; " : "") +
      moneyFlags.length + " untraceable amount(s): " + moneyFlags.join(", ");
  }

  // STEP 5 - OUTPUTS: proposal Doc (with verification report appended),
  // tracker row, Gmail review draft. The human sends, never the script.
  const docUrl = writeProposalDoc_(file.getName(), proposalText, audit, moneyFlags);
  logToSheet_(file.getName(), facts, status, docUrl, notes, startedAt);
  createReviewDraft_(facts, docUrl, status, notes);

  file.moveTo(processedFolder);
}

// ---- GEMINI ----------------------------------------------------------------
function callGemini_(prompt, maxTokens) {
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
    MODEL + ":generateContent?key=" + GEMINI_API_KEY;
  let response, body;
  for (let attempt = 0; attempt < 4; attempt++) {
    response = UrlFetchApp.fetch(url, {
      method: "post",
      contentType: "application/json",
      muteHttpExceptions: true,
      payload: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { responseMimeType: "application/json", maxOutputTokens: maxTokens || 8192 }
      })
    });
    body = response.getContentText();
    if (response.getResponseCode() < 500) break; // retry transient 5xx only
    Utilities.sleep(3000 * (attempt + 1));
  }
  if (response.getResponseCode() !== 200) {
    throw new Error("Gemini API " + response.getResponseCode() + ": " + body.slice(0, 300));
  }
  const json = JSON.parse(body);
  const text = json.candidates[0].content.parts
    .map(p => p.text || "").join("").replace(/```json|```/g, "").trim();
  return JSON.parse(text);
}

function extractFacts_(transcript) {
  const prompt = [
    "You are extracting facts from a sales call transcript for a proposal.",
    "For EVERY field return an object with two keys:",
    '  "value": the fact, or null if the call never states it,',
    '  "quote": the exact verbatim line from the transcript the fact comes from,',
    "           or null if the value is null.",
    "Never paraphrase the quote. Never guess a value the call does not state.",
    "Fields: clientName, clientCompany, companySize, pain, weeklyVolume,",
    "averageJobValue, currentProcess, desiredOutcome, budgetCap, monthlyBudget,",
    "timeline, mustHaves (array of {value, quote}), decisionProcess.",
    "Return ONLY valid JSON.",
    "",
    "TRANSCRIPT:",
    transcript
  ].join("\n");
  return callGemini_(prompt, 8192);
}

function draftProposal_(verifiedFacts, pastProposals) {
  const factLines = verifiedFacts.map(a => "- " + a.field + ": " + a.value +
    ' (from call: "' + a.quote + '")').join("\n");
  const prompt = [
    "Write a consulting proposal as plain text using ONLY the verified call",
    "facts below and the pricing/structure patterns in the past proposals.",
    "Rules:",
    "- Every client-specific fact must come from the verified list. If a",
    "  section needs something the call never stated, write [CONFIRM: ...]",
    "  instead of inventing it.",
    "- Keep the same section skeleton and plain-spoken tone as the past",
    "  proposals: CLIENT CONTEXT, SCOPE OF WORK, TIMELINE, INVESTMENT, WHY US.",
    "- Pricing must stay inside the client's stated cap and follow the shape",
    "  of the past proposals (one-time setup, optional monthly).",
    '- Return JSON: {"proposal": "<full proposal text with \\n newlines>"}',
    "",
    "VERIFIED CALL FACTS:",
    factLines,
    "",
    "PAST PROPOSALS (style and pricing patterns to reuse):",
    pastProposals
  ].join("\n");
  return callGemini_(prompt, 8192).proposal;
}

// ---- DETERMINISTIC VERIFIERS -----------------------------------------------
function norm_(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }

function auditQuotes_(facts, transcript) {
  const t = norm_(transcript);
  const audit = [];
  const check = (field, obj) => {
    if (!obj || obj.value == null) return;
    const ok = obj.quote && t.indexOf(norm_(obj.quote)) !== -1;
    audit.push({ field: field, value: obj.value, quote: obj.quote, ok: !!ok });
  };
  ["clientName","clientCompany","companySize","pain","weeklyVolume",
   "averageJobValue","currentProcess","desiredOutcome","budgetCap",
   "monthlyBudget","timeline","decisionProcess"].forEach(f => check(f, facts[f]));
  (facts.mustHaves || []).forEach((m, i) => check("mustHave[" + i + "]", m));
  return audit;
}

function auditMoneyClaims_(proposalText, transcript, pastProposals) {
  const haystack = norm_(transcript) + " ||| " + norm_(pastProposals);
  const amounts = proposalText.match(/\$[\d,]+(?:\.\d{1,2})?/g) || [];
  const unique = [...new Set(amounts)];
  return unique.filter(a => haystack.indexOf(norm_(a)) === -1);
}

// ---- OUTPUTS ----------------------------------------------------------------
function writeProposalDoc_(sourceName, proposalText, audit, moneyFlags) {
  const facts = (audit.find(a => a.field === "clientName") || {}).value || "Prospect";
  const company = (audit.find(a => a.field === "clientCompany") || {}).value || "";
  const doc = DocumentApp.create("Proposal - " + company + " (" + facts + ")");
  const body = doc.getBody();
  body.appendParagraph(proposalText);
  body.appendHorizontalRule();
  body.appendParagraph("VERIFICATION REPORT (auto-generated)")
      .setHeading(DocumentApp.ParagraphHeading.HEADING2);
  audit.forEach(a => {
    body.appendListItem(
      (a.ok ? "VERIFIED" : "FAILED QUOTE CHECK") + " - " + a.field + ": " +
      a.value + (a.quote ? '  [call: "' + a.quote + '"]' : ""));
  });
  moneyFlags.forEach(m => body.appendListItem("FLAGGED AMOUNT (not in call or past proposals): " + m));
  body.appendListItem("Source transcript: " + sourceName);
  doc.saveAndClose();
  DriveApp.getFileById(doc.getId()).moveTo(DriveApp.getFolderById(OUT_FOLDER_ID));
  return "https://docs.google.com/document/d/" + doc.getId() + "/edit";
}

function logToSheet_(fileName, facts, status, docUrl, notes, startedAt) {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_TAB);
  const v = f => (facts[f] && facts[f].value) || "";
  sheet.appendRow([fileName, v("clientName"), v("clientCompany"),
    status, docUrl, notes || "All checks passed", startedAt, ""]);
}

function createReviewDraft_(facts, docUrl, status, notes) {
  const company = (facts.clientCompany && facts.clientCompany.value) || "new prospect";
  const subject = "Proposal ready for review: " + company;
  const body = [
    "The workflow just turned a call transcript into a proposal.",
    "",
    "Status: " + status + (notes ? " (" + notes + ")" : ""),
    "Proposal (verification report is at the end of the doc):",
    docUrl,
    "",
    "Review it, then send it to the prospect yourself.",
    "Note: the call transcript did not capture the prospect's email address,",
    "so the workflow could not pre-address anything - another reason the",
    "final send stays human."
  ].join("\n");
  GmailApp.createDraft(FOUNDER_EMAIL, subject, body);
}

// ---- HELPERS / SETUP ---------------------------------------------------------
function readFolderTexts_(folder) {
  const out = [];
  const files = folder.getFiles();
  while (files.hasNext()) {
    const f = files.next();
    if (/\.txt$/i.test(f.getName())) {
      out.push("=== " + f.getName() + " ===\n" + f.getBlob().getDataAsString());
    }
  }
  return out.join("\n\n");
}

function getOrCreateSubfolder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

// Run once from the editor: checks the transcript folder every 15 minutes.
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "processNewTranscripts") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("processNewTranscripts").timeBased().everyMinutes(15).create();
}
