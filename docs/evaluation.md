# Evaluation plan

| Case | Input condition | Expected behavior |
|---|---|---|
| Golden path | Company, pain, goal, timeline present | Facts extracted with quotes; draft created |
| Missing budget | No explicit amount | `To be confirmed`; blocker; export locked |
| Historical price trap | Old proposal contains amount | Amount excluded from current draft |
| Explicit budget | Current transcript states amount | Amount preserved with source quote |
| Noisy transcript | Speaker labels and filler | Relevant facts still surfaced; unknowns remain visible |
| Contradiction | Two current-call terms disagree | Field marked conflict; reviewer must choose |

Metrics to capture in a live-model run: median latency, provider/model, estimated input/output tokens, cost per run, extraction precision on golden facts, unsupported-claim count, reviewer correction count.
