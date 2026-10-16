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
