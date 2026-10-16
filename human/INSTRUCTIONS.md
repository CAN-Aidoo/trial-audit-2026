# Blinded human re-check (20% sample)

This check answers the question a reviewer will ask first: *does a human reading the papers get the same
numbers as the AI-assisted extraction?* It only means something if you code from the papers alone.

**Sample.** 19 papers (12 included, 7 excluded in the final data), drawn with seed 20261016 by
`make_packet.py`. The draw is fixed; do not redraw or swap papers.

**Blinding rules.**
- While coding, do not open `data/`, `results/`, `verify/`, `human/sample.json` (it lists which sampled
  papers were included), or the paper's Appendix B table.
- Do not open `2_rows.csv` until Step 1 is finished: it lists rows only for papers the final data include.
- Do not ask an AI model to read or code the papers for you. You may use a PDF viewer, a calculator, and the
  protocol (`PROTOCOL.md`, including D1–D9).
- If you remember a number from earlier work, code what the paper says anyway.

## Step 1: screening (`1_screening.csv`). Finish this for all 19 papers before Step 2.

For each paper, open the link and decide whether to include it. Include it only if all three hold:
- **I1:** the deployed real-robot policy takes force, torque, tactile or actuator-effort (motor current, load,
  joint torque) as **input**.
  - Camera-measured contact deformation counts as tactile.
  - A signal used only as a training reward or for supervision does not count.
- **I2:** there is a real-robot evaluation with a binary success outcome, or one that can be made binary.
  - If a paper reports only partial-credit or progress scores, it fails I2 (D8a).
  - Per-trial binary outcomes count even when they are not labelled "success".
- **I3:** trial counts are stated, or can be recovered, for at least one real-robot comparison with a baseline
  or ablation.
  - If I1 and I2 hold but n is never stated: include = Y and eligible_but_n_missing = Y.

**Exclude:**
- papers posted outside 2026-01-01 to 2026-09-30;
- surveys;
- papers about sensor hardware only;
- simulation-only papers.

**Reporting fields (included papers only, real-robot results):**
- **CI or error bars:** any interval or error bar on a success rate.
- **Significance test:** any significance test.
- **Seeds:** the number of training seeds is stated.
- **Success defined:** there is an explicit success criterion.
- **Randomised initial conditions:** randomised or matched initial conditions are described.
  - Use "unclear" if you cannot tell.

Fill in "minutes spent". It goes in the paper as the cost of a human check.

## Step 2: numbers (`2_rows.csv`)

Code only the papers you included in Step 1.
- If you excluded a paper that appears here, leave its rows blank and write "excluded in step 1" in the notes.

**For every row, fill in from the paper:**
- **nP, sP:** trials and successes of the proposed method. If a variant is named, use that variant.
- **nX, sX:** trials and successes of the named comparator.

**Percentages:**
- If only percentages are given, successes = round(rate × n).
- Mark n_ambiguous = Y if rate × n is not an integer to within 0.5.

**Partial credit:**
- If the task is scored with partial credit, leave sP and sX blank and set outcome = partial.

**Comparator check** ("comparator OK?" = N plus what it should be, if wrong):
- **Kind B** must be the strongest external or author-built baseline on that task. These are not eligible:
  - an ablation that still uses the signal;
  - an oracle;
  - a baseline containing the proposed method's own modules.
- **Kind A** must be the proposed method with the force/touch input removed.

**Missing comparisons:** if you see a real-robot binary comparison the sheet lacks, add a row with
row = "new".

## Step 3: score

```
python3 human/score_human.py
```

This compares your sheets with the final (adjudicated) data. It writes `human/agreement.json`,
`human/discrepancies.csv` and `human/macros_human.tex`.

**For each discrepancy:** re-open the paper and decide who was right.
- Record the decision and the reason in the `resolution` column of `discrepancies.csv`.
- If the final data were wrong, it needs correcting and the analysis re-running.
- Report the agreement **before** resolution in the paper. The script computes it from your untouched sheets,
  so do not edit your sheets after scoring.
