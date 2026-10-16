# Extraction record (one JSON per paper: data/extract/<arxiv_id>.json)
id, title, date, include (bool), exclude_reason (str|null)
signal: force | torque | tactile | current | mixed
reporting: {ci_or_errorbars: bool, sig_test: bool, seeds_reported: bool, success_defined: bool, randomized_init: "yes"|"no"|"unclear"}
comparisons: list of
  {task, outcome, kind: "B" (strongest baseline) | "A" (no-force/touch ablation of the proposed method),
   baseline_name, nP, sP, nX, sX, source (table/page), n_ambiguous (bool), note}
  sP/sX = successes; if only % given: round(rate*n). n_ambiguous if the % is not k/n for integer k.
flags: free-text notes (inconsistencies are recorded neutrally)
RULE (2026-10-16, before 2nd paper): every reported task/condition row is extracted, including ties.
