# Audit protocol (frozen before data extraction)

Working title: *How Many Trials Back a Force-Aware Manipulation Claim? A Statistical Audit of Real-Robot Evaluations, 2024-2026*

Author: Clement Aidoo (CANLABS). Protocol version 1.0, frozen 2026-10-16, before any success rate was extracted.
Any later change is listed in "Deviations" at the end, with date and reason.

## 1. Question
In real-robot evaluations of manipulation methods that use force, torque, tactile, or actuator-effort (motor current / load) signals:
1. How many trials per condition are reported?
2. How often are uncertainty (CIs, error bars, seeds) or significance tests reported?
3. For the headline comparisons (proposed method vs. the strongest baseline, and vs. the same method without the force/touch signal), how many differences remain distinguishable from zero under standard binomial statistics?
4. How many trials would each comparison have needed?

The audit is about evaluation practice in the field, not about the merit of any individual paper. A comparison that is not statistically resolved is not evidence that the method does not work.

## 2. Sources and search (fixed)
Database: arXiv (searched via alphaXiv), first version posted 2024-01-01 to 2026-09-30.
Fixed queries (run once each; all hits screened):
- Q1 "force-aware manipulation policy real robot"
- Q2 "tactile imitation learning contact-rich manipulation"
- Q3 "force torque feedback visuomotor policy"
- Q4 "force vision-language-action model"
- Q5 "motor current proprioceptive contact manipulation low-cost robot"
- Q6 "visuo-tactile policy learning dexterous manipulation"
Additional seed papers named in the planning report (Current as Touch, FACTR, FACTR 2, NeuralActuator, CoPRE, ForceRFT, DexForce, ForceVLA, TA-VLA, FD-VLA, Opt2VLA, DexFruit) are screened with the same criteria and flagged `source=seed`.

## 3. Inclusion criteria (all must hold)
I1. Proposes or evaluates a manipulation method (policy, controller, or learning pipeline) whose input includes force, torque, tactile, or actuator-effort signals.
I2. Reports a real-robot evaluation with a binary (or binarisable) success outcome.
I3. Reports, or allows recovery of, the number of trials per condition for at least one comparison between the proposed method and a baseline or ablation.

Exclusion: sensor-hardware-only papers; simulation-only evaluations; surveys; papers whose only real-robot metric is continuous (e.g. force error) with no success outcome; duplicate versions (keep latest arXiv version).

## 4. Extraction fields (per paper, per task)
- paper id, title, date, venue if stated
- task name; trials per condition (n); whether n differs between conditions
- successes (or rate x n, rounded to integer) for: proposed method (P); strongest baseline by reported rate (B); no-force/no-touch ablation of the proposed method (A), if present
- whether the paper reports: CIs or error bars on success; any significance test; number of training seeds; randomised or matched initial conditions; explicit success definition
- source location (table/figure/page) for every number
Rule: if only a percentage is given and n is stated, successes = round(rate x n); if the rounding is ambiguous, flag it. If n is not recoverable, the task is excluded from the statistical analysis but counted in reporting statistics.

## 5. Analyses (fixed)
A1. Distribution of n per condition (median, IQR, fraction with n <= 10, <= 20).
A2. Reporting rates for CIs/error bars, tests, seeds, success definition.
A3. For each task comparison P vs B and P vs A: Wilson 95% CI per arm; Newcombe 95% CI for the difference; two-sided Fisher exact p-value (Boschloo as sensitivity). Report the share of comparisons whose difference CI excludes 0.
A4. Paper-level: share of papers where at least one / the majority / all headline comparisons are resolved at alpha = 0.05 (unadjusted), and after Holm correction within paper.
A5. Required trials: for each comparison, n per arm for 80% power (two-sided, alpha = 0.05, arcsine approximation, checked with exact simulation) at the observed rates; and minimum detectable difference at the reported n with baseline at the observed B rate.
A6. Null simulation: when two methods have the same true success rate, how often does a study with k tasks, n trials each, and selection of the best of m baselines show an apparent improvement of >= 10 / 20 points? Grid: n in {5,10,20,50}, k in {1,3,5}, p in {0.3,0.5,0.7}.
A7. Sequential testing illustration (SPRT / STEP-style) showing expected trials to a decision at typical effect sizes.

## 6. Ethics and framing
- Neutral language; no ranking or naming of "worst" papers in the main text. Per-paper extractions are released as data so anyone can check them.
- Extractions are double-checked against the source before release.
- Authors of included papers may be contacted with their extracted numbers before posting, and corrections will be incorporated.

## Deviations


D1 (2026-10-16, before any extraction). The search tool caps searches per call and ranks recent work first, so
nearly all hits from Q1-Q6 are from 2026 (Feb-Sep). To avoid claiming coverage we do not have, the audit window is
narrowed to papers first posted 2026-01-01 to 2026-09-30, and the study is described as a snapshot of 2026 work
retrieved by fixed queries, not a census of 2024-2026. Seed papers outside the window (FACTR 2502.17432,
DexFruit 2508.07118) are excluded on date. Two pilot searches (each combining several queries) were run before Q1-Q6;
papers found only by the pilots are logged but not screened, since the pilots are not protocol queries.
Raw hits: data/raw_hits.py.

D2 (2026-10-16, during extraction of paper 3 of 87; no analysis run yet). Two coding rules added where the protocol was silent:
(a) Tasks scored with partial credit (e.g. 0.5 per trial) are not binomial; they are recorded and counted in the
    trial-count and reporting statistics (A1, A2) but excluded from the binomial tests (A3-A5).
(b) Kind "A" (no-signal ablation) is used only when the paper evaluates its own method with the force/touch input
    removed. A separate baseline that merely lacks touch (e.g. a visuomotor policy with a different design) is coded
    as a candidate for kind "B" only. If the paper itself identifies a baseline as its own method's no-force
    component (e.g. "our global vision policy"), it is coded as "A".

D3 (2026-10-16, during extraction, no analysis run). Clarifies a conflict between I3 and Section 4: a paper that is
otherwise eligible but never states trial counts fails I3 and is excluded from the tests, but is kept in the data as
"eligible_but_n_missing" and counted in the reporting statistics (A2), since missing n is itself a reporting outcome.

D4 (2026-10-16, during extraction of paper 47 of 89; no analysis run). I1 clarification where the protocol was
silent: a policy input that measures contact-induced deformation with a camera (e.g. an external camera tracking the
deformation field of a compliant finger, analogous to GelSight-type optical tactile sensors) counts as "tactile".
Tactile signals generated from RGB by a learned model also count when the policy consumes them through a tactile
channel (applies to 2607.20683 FELT, coded earlier under the same reading). Both are flagged in the records.

D5 (2026-10-16, during extraction; no analysis run). Makes explicit a rule applied since D2b: candidates for kind "B"
are external or author-built baselines, not ablations of the proposed method that still use the force/touch signal,
and not oracle variants of the proposed method (e.g. the same method fed ground-truth sensor data). Baselines that
include a component of the proposed method are also excluded from B and noted in the record. To be re-checked for
all records during independent verification (task 16).

D6 (2026-10-16, during extraction of paper 85 of 89; no analysis run). I1 clarification where the protocol was
silent: the force/touch/effort signal must be an input to the policy or controller as deployed on the real robot.
Methods that use such signals only as a training reward or training-time supervision, with a deployed policy that
does not receive them, fail I1 (applies to 2609.33882 DexTaG, coded earlier under the same reading, and 2609.36785
TaRL). To be re-checked for all earlier records during independent verification (task 16).

D7 (2026-10-16, after extraction finished, before any analysis was run). Rules the protocol left open, fixed before
analyze.py was first executed:
(a) Multiple proposed variants or duplicate rows for the same (paper, task, kind): the primary analysis keeps the
    first-listed row, which follows the order of the paper's own results table (its main configuration). The
    all-rows set is reported as a sensitivity analysis. Rows pooled across tasks are kept (they never duplicate a
    per-task row) and flagged.
(b) A3-A5 use binary rows only (outcome "success"); other outcomes are counted in A1/A2 only (extends D2a).
(c) A4 Holm family = all primary binary comparisons of one paper (kinds A and B together); results are also
    reported by kind.
(d) A6 "best of m": m is read as the number of candidate configurations of the proposed method from which the best
    is reported against one shared baseline (the pattern seen in 2609.30969); m in {1, 3, 5}. Apparent improvement
    = mean over the k tasks of (best variant - baseline), in percentage points. 200,000 replicates, seed 20261016.
(e) A5 check: power of the two-sided Fisher exact test at the arcsine-approximation n is computed exactly by
    enumerating all tables (rather than by Monte Carlo); the exact Fisher required n is also reported.
(f) A7: Wald SPRT on discordant pairs of alternating P/X trials (H0 theta = 0.5), one-sided alpha = 0.025,
    beta = 0.2, designed for pX = 0.5 vs pP = 0.7, truncated at 500 pairs; 20,000 replicates per true effect.
(g) Sensitivity: primary set excluding rows flagged n_ambiguous.

D8 (2026-10-16, during independent verification). Note on timing: analyze.py had been run once on the
unverified data (results not reported) before these rules were written; they were prompted by the blinded
verifiers' screening and are applied uniformly. (a) I2 clarification: a paper whose real-robot outcomes are all
partial-credit or progress scores, with no binary or binarisable success outcome, fails I2 (D2a continues to govern
partial-credit tasks in papers that also report binary outcomes). Per-trial binary outcomes that are not labelled
"success" (e.g. "no grasp failure", "stable") are binary and enter the tests. (b) Reporting fields: for the two
judgement fields (randomized_init, success_defined), a coder disagreement that was not resolved by re-reading the
paper is coded conservatively ("unclear" / false). (c) All other disagreements are resolved by checking the source;
every change is logged in verify/adjudication_log.json with its reason.

D9 (2026-10-16, after results, in response to internal review). Timing: written after all results in the
draft were known; it changes how A5 is summarised, not any data or test. Reason: A5 as planned evaluates power at
each comparison's observed rates, which is a monotone function of the comparison's own p-value (post hoc power;
Hoenig & Heisey 2001) and is inflated further when observed gaps are selected. (a) The reported A5 summary is now
the exact two-sided Fisher power (alpha 0.05, equal arms of the smaller reported n) to detect pre-set gains of
+15, +20 and +30 points over the comparator's observed rate (comparator rate capped at 1 - gain), plus the
minimum detectable difference. (b) The accuracy of the arcsine sample-size formula is reported on a fixed design
grid (comparator rate 0.1/0.3/0.5/0.7 x gain 15/20/30 points, improved rate <= 0.95), not at observed rates.
(c) The observed-rate quantities remain in results/comparisons.csv and summary.json and are not interpreted.

D10 (2026-10-18, after version 1 was posted). Human re-check: the author re-coded a seeded 20% sample (19 papers:
12 included, 7 excluded; human/sample.json) from the papers alone, screening first, using human/INSTRUCTIONS.md.
Sheets were hash-locked before scoring (human/screening.sha256.json, human/sheets.sha256.json). Disagreements were
resolved against the source (human/screening_discrepancies.csv, human/discrepancies.csv, human/resolution_log.json):
three kind-B comparator names on a partial-credit task changed (no effect on tests); two comparisons missing from the
extraction were added (2609.37433, Insert Peg under full fine-tuning; n from the paper's stated default, flagged
n_ambiguous); two further missing comparisons had no per-task counts and were not added.

D11 (2026-10-25, after version 2 was posted; first author response). Following Section 6, Chenguang Yang
(corresponding author of 2609.05832) checked that paper's extraction. Changes: (a) the record noted no comparisons
and n = 24-25; the authors state that Fig. 6 reports six binary-success conditions and that most bars average
several batches of about 25 trials, so per-condition n is not recoverable. The paper is recoded as
eligible_but_n_missing (D3): its comparisons stay out of the tests and it no longer contributes n = 24-25 to A1.
(b) The authors point to success criteria and initial-condition ranges in the supplementary video of the journal
version. The audit's source is the arXiv PDF (Section 2), so these reporting items keep their arXiv-text coding;
the scope is now stated in the paper's Limitations. Author replies and resulting changes are logged in
authors/log.csv.
