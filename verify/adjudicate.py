"""Apply adjudicated corrections to data/extract/*.json and log every change.

Each decision was checked against the source paper by the adjudicator unless marked "rule:", in which case it
follows a written rule (protocol D2-D8). Run once: python3 verify/adjudicate.py  (idempotent: refuses to re-run).
Writes verify/adjudication_log.json and verify/macros_verify.tex.
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "extract")
LOG = os.path.join(ROOT, "verify", "adjudication_log.json")
if os.path.exists(LOG):
    raise SystemExit("adjudication already applied")

recs = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(D, "*.json"))}
log = []


def note(pid, what, why):
    log.append(dict(paper=pid, change=what, reason=why))


def row(pid, i):
    return recs[pid]["comparisons"][i]


def set_row(pid, i, why, **kw):
    c = row(pid, i)
    old = {k: c.get(k) for k in kw}
    c.update(kw)
    note(pid, f"row {i} ({c['task']}, {c['kind']}): {old} -> {kw}", why)


drop = {}  # pid -> set of row indices to delete at the end


def drop_row(pid, i, why):
    c = row(pid, i)
    drop.setdefault(pid, set()).add(i)
    note(pid, f"row {i} removed ({c['task']}, {c['kind']}, vs {c['baseline_name']})", why)


def add_row(pid, why, **c):
    base = dict(outcome="success", n_ambiguous=False, note="")
    base.update(c)
    recs[pid]["comparisons"].append(base)
    note(pid, f"row added: {c['task']} {c['kind']} vs {c['baseline_name']} "
              f"{c['sP']}/{c['nP']} vs {c['sX']}/{c['nX']}", why)


# ---------------- inclusion
r = recs["2603.13869"]
r.update(include=True, exclude_reason=None, eligible_but_n_missing=True, n_values=[])
note("2603.13869", "include False -> True, eligible_but_n_missing",
     "rule D3: eligible papers that never state n are kept as eligible_but_n_missing, not excluded (first coding "
     "applied I3 exclusion, inconsistent with D3)")
for pid in ["2606.17055", "2609.34182", "2606.12406", "2609.15012", "2609.20649"]:
    r = recs[pid]
    r.update(include=False, exclude_reason="I2 (D8): all real-robot outcomes are partial-credit or progress scores; "
                                           "no binary or binarisable success outcome reported")
    note(pid, "include True -> False", "D8: verifier screening; papers with only partial-credit outcomes fail I2")

# ---------------- kind B choices (D5) and comparator corrections, checked against source
set_row("2602.22088", 2, "D5: RISE-2 is Force Policy's own global vision module ('our global vision policy'); "
        "strongest eligible are pi0.5 and RDP, 7/10 (Table II)", baseline_name="pi0.5 / RDP (tie)", sX=7)
set_row("2602.22088", 6, "D5: RISE-2 ineligible as B; TA-VLA has the same count", baseline_name="TA-VLA")
set_row("2602.22088", 12, "D5: RISE-2 ineligible as B; pi0.5 has the same count", baseline_name="pi0.5")
for i, sx in zip((0, 2, 4, 6), (9, 14, 24, 14)):
    set_row("2607.22530", i, "D5: pi0.5+tactile expert-only is the proposed pipeline without ViTacWorld data and "
            "still uses touch; strongest eligible B is pi0.5 vision-only expert-only (Table I: 18/28/48/28% of 50)",
            baseline_name="pi0.5 (vision-only), expert-only data", sX=sx)
for i, sx in zip(range(4), (21, 20, 22, 15)):
    set_row("2606.09337", i, "D5: RLT uses TORL-VLA's frozen wrench-aware reference model (App. A.3.1); strongest "
            "eligible B is ForceVLA (Table 1)", baseline_name="ForceVLA", sX=sx)
set_row("2609.12549", 0, "LDA-1B-Dex 0.40 (8/20) exceeds pi0.5 0.15 on earbud flipping (Table I); pi0.5-Dex w/o "
        "STAR is a touch-using ablation (D5)", baseline_name="LDA-1B-Dex", sX=8)
set_row("2606.06281", 6, "Sparsh-X V+G scores 20% (4/20) on Key in Lock, above V+G+E 10% (Table 7)",
        baseline_name="Sparsh-X V+G", sX=4)
for i in (0, 2):
    set_row("2609.14156", i, "Plain pi0.5 Baseline 20/30 exceeds Tac-View 16/30 on Lift (Table 15); Position-Only "
            "uses the proposed overlay pipeline (D5)", baseline_name="Baseline (pi0.5, no contact input)", sX=20)
for i in (2, 3):
    set_row("2609.15921", i, "D5: DP Proprio+Tactile shares the proposed frozen ViT-MAE tactile encoder (Sec. 4.2); "
            "strongest eligible B is DP Proprio, 0% SR@10 and SR@20 (Table 1)",
            baseline_name="DP Proprio (no tactile)", sX=0, note="")
set_row("2608.01824", 7, "Tactile-VLA 25.0 exceeds pi0.5+tactile 15.0 (partial-credit row; name only)",
        baseline_name="Tactile-VLA")
for i in range(9):
    drop_row("2608.01102", i, "D5: every real-world baseline (Gate, Concat) includes Dynamic Tactile Masking, one "
             "of CAAT's two proposed components; no eligible B")
drop_row("2606.30988", 1, "D5: the Diffusion Policy comparator is trained with MuSe's continual-learning pipeline "
         "including F/T (an ablation that still uses the signal)")
drop_row("2606.30988", 2, "D5: 'Pretraining Only' is MuSe's own pretrained model, still using F/T")
set_row("2606.30988", 4, "'No F/T' is the method without F/T: kind A, not B (D2b)", kind="A")
for i in (1, 3, 5, 7):
    drop_row("2606.14218", i, "D5: the No-torque comparator is the method's own policy with torque removed (coded as "
             "kind A); it contains the proposed method's components and is not eligible as B")
for i in (1, 3, 5, 7):
    drop_row("2607.03723", i, "PLD (visual only) is the original PLD method, not OmniTacTune with touch removed "
             "(verifier; confirmed App. A.3)")
for t, sp, sx in (("Peg-in-hole", 20, 8), ("Charger insertion", 20, 2), ("Cap opening", 18, 1),
                  ("Box opening", 17, 1)):
    add_row("2607.03723", "frozen visual base policy = OmniTacTune with the tactile residual removed; base success "
            "40/10/5/5% over 20 trials (Sec. 4.1)", task=t, kind="A",
            baseline_name="Frozen visual base policy (no tactile residual)", nP=20, sP=sp, nX=20, sX=sx,
            source="Sec. 4.1 p7; Table 1")
for i in range(15, 20):
    drop_row("2610.00638", i, "pretrained variant vs InternVLA-A1 confounds touch with extra visuo-tactile "
             "pretraining; not a no-signal ablation of that variant")
drop_row("2608.25872", 11, "n for unseen-scale tests not stated (verifier); assumed n not recoverable (I3 rule)")
drop_row("2608.25872", 13, "n for unseen-scale tests not stated (verifier); assumed n not recoverable (I3 rule)")

# ---------------- outcome labels and n for Current as Touch
for i in range(4):
    set_row("2607.03529", i, "per-grasp binary outcome (no grasp failure); paper states 15 trials per user but "
            "rates are multiples of 1/60, consistent with 4 grasps per stacking trial; kept n=60 grasps, flagged "
            "ambiguous (grasps within a trial are not independent)", outcome="success", n_ambiguous=True)
for i in range(8, 12):
    set_row("2607.03529", i, "per-trial binary outcome (stable vs slipped/fell)", outcome="success")
add_row("2607.03529", "missing row reported by verifier; Table 4 tolerant success 90.4% vs 65.4% of 52",
        task="single-card picking (tolerant)", kind="A", baseline_name="w/o Current (ACT baseline)",
        nP=52, sP=47, nX=52, sX=34, source="Table 4 p7")
add_row("2609.20980", "missing A rows reported by verifier: fine-tuned VLA without tactile, pooled 4 tasks x 20",
        task="Low illumination, 4 tasks pooled", kind="A", baseline_name="w/o Tactile", nP=80, sP=64, nX=80, sX=32,
        source="robustness table (40.0% of 80)")
add_row("2609.20980", "as above", task="Visual clutter, 4 tasks pooled", kind="A", baseline_name="w/o Tactile",
        nP=80, sP=65, nX=80, sX=22, source="robustness table (27.5% of 80)")

# ---------------- reporting fields
rep = [("2609.14156", "ci_or_errorbars", False, "real-robot table reports counts only; error bars are on LIBERO "
        "simulation results"), ("2609.14156", "seeds_reported", False, "seeds stated for simulation only"),
       ("2609.16504", "seeds_reported", False, "real-robot policy seeds not stated (5 evaluation seeds in sim)"),
       ("2609.15921", "ci_or_errorbars", True, "mean +/- std across 3 seeds (Sec. 5.1)"),
       ("2609.15921", "seeds_reported", True, "3 seeds x 10 rollouts"),
       ("2609.30969", "ci_or_errorbars", True, "SD shown in the average column of Fig. 3 (verifier)"),
       ("2609.36596", "seeds_reported", True, "single seed (42) stated"),
       ("2607.03723", "success_defined", False, "task goals described but no explicit success criterion (checked)")]
for pid, f, v, why in rep:
    old = recs[pid]["reporting"][f]
    recs[pid]["reporting"][f] = v
    note(pid, f"reporting.{f}: {old} -> {v}", why)
# rule D8b: unresolved disagreements on the two judgement fields are coded conservatively
for pid, f in [("2607.18231", "randomized_init"), ("2608.01824", "randomized_init"), ("2609.37433", "randomized_init"),
               ("2606.04825", "randomized_init"), ("2606.11767", "randomized_init"), ("2606.06281", "randomized_init"),
               ("2606.08555", "randomized_init"), ("2609.14156", "randomized_init"),
               ("2606.04825", "success_defined"), ("2606.06281", "success_defined"),
               ("2606.13232", "success_defined")]:
    old = recs[pid]["reporting"][f]
    new = "unclear" if f == "randomized_init" else False
    recs[pid]["reporting"][f] = new
    note(pid, f"reporting.{f}: {old} -> {new}", "rule D8b: unresolved coder disagreement on a judgement field "
         "coded conservatively")

# ---------------- apply drops, recompute n_values, write
for pid, idx in drop.items():
    recs[pid]["comparisons"] = [c for i, c in enumerate(recs[pid]["comparisons"]) if i not in idx]
for pid, r in recs.items():
    if r["include"] and not r.get("eligible_but_n_missing") and r["comparisons"]:
        ns = sorted({c[k] for c in r["comparisons"] for k in ("nP", "nX") if c[k]})
        if ns:
            r["n_values"] = sorted(set(r["n_values"]) | set(ns))
    r.setdefault("flags", []).append("Verified by blinded second extraction; see verify/adjudication_log.json")
    json.dump(r, open(os.path.join(D, pid + ".json"), "w"), indent=1)
json.dump(log, open(LOG, "w"), indent=1)

# ---------------- macros for the paper
ag = json.load(open(os.path.join(ROOT, "verify", "agreement.json")))
rows_changed = sum(1 for e in log if e["change"].startswith(("row",)))
papers_changed = len({e["paper"] for e in log if e["change"].startswith("row")})
incl_changed = sum(1 for e in log if e["change"].startswith("include"))
num = ag["numeric"]
M = dict(VerScreened=ag["screened"], VerIncAgree=ag["include_agree"], VerKappa=f"{ag['include_kappa']:.2f}",
         VerRows=num["rows"], VerExactPct=f"{100 * num['binary_exact'] / num['binary_rows']:.1f}\\%",
         VerOutcomePct=f"{100 * num['outcome_agree'] / num['rows']:.0f}\\%",
         VerBFlag=num["b_flagged"], VerAFlag=num["a_flagged"], VerCorrectedRows=rows_changed,
         VerCorrectedPapers=papers_changed, VerInclChanged=incl_changed)
with open(os.path.join(ROOT, "verify", "macros_verify.tex"), "w") as fh:
    fh.write("% generated by verify/adjudicate.py\n")
    for k, v in M.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(json.dumps(M, indent=1), len(log), "log entries")
