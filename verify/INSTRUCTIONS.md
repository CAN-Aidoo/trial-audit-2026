# Independent verification of a literature audit — instructions for verifier K

You are an independent second extractor for a statistical audit of real-robot evaluations in force/tactile/
current-aware robot manipulation papers (arXiv, posted 2026-01-01 to 2026-09-30). You have NOT seen the first
extractor's numbers or decisions, and must not look for them: do not open anything under data/, results/, or
any file in verify/ other than the two packet files named below and this file. Work only from the papers.

Read the papers with the alphaXiv tools (load them via ToolSearch with query "alphaXiv", then use
mcp__alphaXiv__answer_pdf_queries with paper = the arXiv id, or mcp__alphaXiv__get_paper_content). Useful queries:
"Real-robot experiment results table with success rates per task and method", "Number of trials per method per
task", "Ablation without force/tactile input", "Error bars, confidence intervals, or statistical significance
tests", "Definition of task success".

## Step 1 — screening (do this first, for every paper in verify/packets/batch_K_screen.json)

Decide include true/false from the paper alone. Include only if ALL hold:
- I1. The method evaluated is a manipulation policy/controller/learning pipeline whose input, AS DEPLOYED ON THE
  REAL ROBOT, includes force, torque, tactile, or actuator-effort (motor current/load/joint torque) signals.
  Camera-measured contact deformation (GelSight-like, or an external camera tracking a compliant finger) counts as
  tactile. A signal used only as a training reward or training supervision does NOT count.
- I2. There is a real-robot evaluation with a binary (or binarisable) success outcome. Simulation-only, or
  real-robot results with only continuous metrics (force error, RMSE), fail I2.
- I3. Trial counts per condition are reported or recoverable for at least one real-robot comparison between the
  proposed method and a baseline or ablation. (If everything else holds but n is never stated, set include true
  and eligible_but_n_missing true.)
Exclude also: surveys, sensor-hardware-only papers, pure perception/detection papers with no manipulation
success outcome.

Also record for each INCLUDED paper the reporting fields (about the real-robot results):
ci_or_errorbars (any CI or error bars on success), sig_test (any significance test), seeds_reported (number of
training seeds stated), success_defined (explicit success criterion), randomized_init ("yes" | "no" | "unclear").

Write screening results to verify/out/batch_K_screen.json BEFORE opening the rows file:
[{"id":..., "include": bool, "reason": "which criterion fails, or 'meets I1-I3'", "signal": "...",
  "reporting": {...} or null, "eligible_but_n_missing": bool}]

## Step 2 — numbers (verify/packets/batch_K_rows.json)

For each listed row, find the real-robot result in the paper and fill in, from the source:
nP, sP (trials and successes of the proposed method), nX, sX (trials and successes of the named comparator).
"P" = the paper's proposed method; if note_P_variant names a variant, use that variant. "comparator" is named.
Rules: if only a percentage and n are given, successes = round(rate x n) and set n_ambiguous true when rate x n
is not (within 0.5 points) an integer. If the outcome is scored with partial credit (0.5 per trial, stage scores,
completion fractions), set sP/sX null and outcome "partial credit". Record the table/figure/page used.

Then judge the coding of the row (these are the audit's rules; report disagreements, do not fix silently):
- kind "B" = strongest comparator by reported rate among external or author-built baselines. NOT eligible as B:
  ablations of the proposed method that still use the force/touch signal; oracle variants of the proposed method;
  baselines containing the proposed method's own modules. Is the named B eligible, and is it the strongest
  eligible one for that task? (b_ok: true/false, b_should_be: name or null)
- kind "A" = the proposed method itself with the force/touch input removed (or a baseline the paper itself
  identifies as its own method without force/touch). Is the named A such an ablation? (a_ok: true/false)
- outcome_ok: is the outcome type (binary "success" vs partial credit) coded correctly?

Write verify/out/batch_K_rows.json:
[{"id":..., "row": <row index>, "task":..., "nP":..., "sP":..., "nX":..., "sX":..., "outcome": "success"|"partial credit",
  "n_ambiguous": bool, "source": "...", "b_ok": bool|null, "b_should_be": str|null, "a_ok": bool|null,
  "outcome_ok": bool, "comment": "anything notable, e.g. text/table inconsistency"}]
Also list in an extra object {"id":..., "missing_rows": [...]} any real-robot binary task comparison in the
paper that the packet does not list.

Be literal and careful: copy numbers exactly as the paper reports them. If you cannot find a number, write null
and say why in comment. Do not guess. When finished, reply with a 3-line summary (papers screened, rows checked,
rows where you could not find numbers).
