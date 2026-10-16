"""Run analyses A1-A7 of PROTOCOL.md (v1.0 with deviations D1-D7) on data/extract/*.json.

Usage:  python3 analyze.py            (writes results/)
Outputs:
  results/comparisons.csv      one row per binary comparison, all statistics (primary flag marks the D7a set)
  results/conditions.csv       trial counts per condition (A1)
  results/papers.csv           per-paper reporting fields and resolved-comparison counts (A2, A4)
  results/null_sim.csv         A6 grid
  results/sprt.csv             A7
  results/summary.json         every headline number
  results/macros.tex           the same numbers as LaTeX macros for the paper
"""
import csv
import glob
import json
import math
import os
import re
import sys
import time
from collections import defaultdict

import numpy as np

import stats as S

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ load and validate
records = []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "extract", "*.json"))):
    r = json.load(open(f))
    records.append(r)
included = [r for r in records if r["include"]]

problems = []
for r in included:
    for c in r["comparisons"]:
        for arm in ("P", "X"):
            n, s = c["n" + arm], c["s" + arm]
            if n is not None and n <= 0:
                problems.append((r["id"], c["task"], f"n{arm}<=0"))
            if s is not None and not (0 <= s <= n):
                problems.append((r["id"], c["task"], f"s{arm} out of range"))
        if c["outcome"] == "success" and (c["sP"] is None or c["sX"] is None):
            problems.append((r["id"], c["task"], "binary row without counts"))
if problems:
    sys.exit(f"Data validation failed: {problems}")
log(f"{len(records)} records, {len(included)} included, data validated")


def p_variant(note):
    m = re.match(r"P = ([^;]+)", note or "")
    return m.group(1).strip() if m else ""


# ------------------------------------------------------------------ binary comparison rows
rows = []
seen = set()
for r in included:
    for i, c in enumerate(r["comparisons"]):
        if c["outcome"] != "success":
            continue
        key = (r["id"], c["task"], c["kind"])
        primary = key not in seen          # D7a: first-listed row per (paper, task, kind)
        seen.add(key)
        rows.append(dict(paper=r["id"], title=r["title"], signal=r["signal"], task=c["task"], kind=c["kind"],
                         baseline=c["baseline_name"], p_variant=p_variant(c["note"]),
                         nP=c["nP"], sP=c["sP"], nX=c["nX"], sX=c["sX"], amb=bool(c["n_ambiguous"]),
                         pooled="pooled" in c["task"].lower(), primary=primary, source=c["source"]))
log(f"{len(rows)} binary rows, {sum(r['primary'] for r in rows)} primary")

# ------------------------------------------------------------------ A3 + A5 per row
power_cache = {}
for k, row in enumerate(rows):
    nP, sP, nX, sX = row["nP"], row["sP"], row["nX"], row["sX"]
    pP, pX = sP / nP, sX / nX
    row.update(pP=pP, pX=pX, diff=pP - pX)
    row["wP_lo"], row["wP_hi"] = S.wilson(sP, nP)
    row["wX_lo"], row["wX_hi"] = S.wilson(sX, nX)
    row["nc_lo"], row["nc_hi"] = S.newcombe(sP, nP, sX, nX)
    row["ci_excludes_0"] = row["nc_lo"] > 0 or row["nc_hi"] < 0
    row["fisher_p"] = S.fisher_p(sP, nP, sX, nX)
    row["boschloo_p"] = S.boschloo_p(sP, nP, sX, nX)
    row["n_arcsine"] = S.n_arcsine(pP, pX)
    row["n_reported_per_arm"] = min(nP, nX)
    row["mdd"] = S.mdd_arcsine(pX, nP, nX)
    # exact Fisher check (D7e) on primary rows with a finite, moderate requirement
    row["power_exact_at_arcsine_n"] = float("nan")
    row["n_fisher_exact"] = float("nan")
    if row["primary"] and math.isfinite(row["n_arcsine"]) and row["n_arcsine"] <= 400:
        key = (round(pP, 6), round(pX, 6))
        if key not in power_cache:
            na = row["n_arcsine"]
            pw = S.fisher_power_exact(pP, pX, na)
            # exact required n: binary search on [ceil(0.7 na), 2 na] (power is near-monotone in n)
            lo, hi = max(2, int(0.7 * na)), max(8, 2 * na)
            while hi < 600 and S.fisher_power_exact(pP, pX, hi) < 0.8:   # widen until power is reached
                lo, hi = hi, min(600, 2 * hi)
            if S.fisher_power_exact(pP, pX, hi) < 0.8:
                nf = float("inf")
            else:
                while lo < hi:
                    mid = (lo + hi) // 2
                    if S.fisher_power_exact(pP, pX, mid) >= 0.8:
                        hi = mid
                    else:
                        lo = mid + 1
                nf = lo
            power_cache[key] = (pw, nf)
        row["power_exact_at_arcsine_n"], row["n_fisher_exact"] = power_cache[key]
    if (k + 1) % 50 == 0:
        log(f"  stats for {k + 1}/{len(rows)} rows")

# Holm within paper (D7c), for each analysis set separately
for setname, sel in (("primary", lambda r: r["primary"]), ("all", lambda r: True)):
    by_paper = defaultdict(list)
    for r in rows:
        if sel(r):
            by_paper[r["paper"]].append(r)
    for rs in by_paper.values():
        adj = S.holm([r["fisher_p"] for r in rs])
        for r, a in zip(rs, adj):
            r[f"holm_p_{setname}"] = a
for r in rows:
    r.setdefault("holm_p_primary", float("nan"))

log("A3/A5 done")


# ------------------------------------------------------------------ summaries
def frac(x):
    x = list(x)
    return (sum(x) / len(x)) if x else float("nan")


def comp_summary(rs):
    rs = list(rs)
    fin = [r for r in rs if math.isfinite(r["n_arcsine"])]
    ratio = [r["n_arcsine"] / r["n_reported_per_arm"] for r in fin]
    pw = [r["power_exact_at_arcsine_n"] for r in rs if not math.isnan(r["power_exact_at_arcsine_n"])]
    mdd = [r["mdd"] for r in rs]
    return dict(
        n=len(rs),
        p_gt=frac(r["diff"] > 0 for r in rs), p_eq=frac(r["diff"] == 0 for r in rs),
        p_lt=frac(r["diff"] < 0 for r in rs),
        median_diff_pts=float(np.median([r["diff"] for r in rs]) * 100) if rs else float("nan"),
        ci_excludes_0=frac(r["ci_excludes_0"] for r in rs),
        ci_excludes_0_favouring_P=frac(r["nc_lo"] > 0 for r in rs),
        fisher_sig=frac(r["fisher_p"] < 0.05 for r in rs),
        boschloo_sig=frac(r["boschloo_p"] < 0.05 for r in rs),
        n_required_median=float(np.median([r["n_arcsine"] for r in fin])) if fin else float("nan"),
        n_required_iqr=[float(np.percentile([r["n_arcsine"] for r in fin], q)) for q in (25, 75)] if fin else None,
        share_equal_rates=frac(not math.isfinite(r["n_arcsine"]) for r in rs),
        share_reported_n_adequate=frac(r["n_reported_per_arm"] >= r["n_arcsine"] for r in rs),
        median_ratio_required_to_reported=float(np.median(ratio)) if ratio else float("nan"),
        exact_power_at_arcsine_n_mean=frac(pw), exact_power_at_arcsine_n_min=min(pw) if pw else float("nan"),
        n_exact_checked=len(pw),
        share_exact_power_below_0p7=frac(x < 0.7 for x in pw),
        n_fisher_exact_median=float(np.median([r["n_fisher_exact"] for r in rs
                                               if not math.isnan(r["n_fisher_exact"])])) if pw else float("nan"),
        share_reported_n_adequate_exact=frac(r["n_reported_per_arm"] >= r["n_fisher_exact"] for r in rs
                                             if not math.isnan(r["n_fisher_exact"])),
        mdd_median_pts=float(np.nanmedian(mdd) * 100) if rs else float("nan"),
        mdd_undetectable_share=frac(math.isnan(m) for m in mdd),
    )


prim = [r for r in rows if r["primary"]]
A3 = {
    "primary_all": comp_summary(prim),
    "primary_B": comp_summary(r for r in prim if r["kind"] == "B"),
    "primary_A": comp_summary(r for r in prim if r["kind"] == "A"),
    "all_rows": comp_summary(rows),
    "primary_excl_ambiguous": comp_summary(r for r in prim if not r["amb"]),
    "primary_excl_pooled": comp_summary(r for r in prim if not r["pooled"]),
}

# relative change Fisher vs Boschloo disagreement
A3["fisher_boschloo_disagree"] = sum((r["fisher_p"] < 0.05) != (r["boschloo_p"] < 0.05) for r in prim)
# exact-vs-arcsine required n
ex = [(r["n_fisher_exact"], r["n_arcsine"]) for r in prim if not math.isnan(r["n_fisher_exact"])
      and math.isfinite(r["n_fisher_exact"])]
A3["exact_over_arcsine_n_median"] = float(np.median([a / b for a, b in ex])) if ex else float("nan")


# ------------------------------------------------------------------ A4 paper level
def paper_level(rs, holm_key):
    by = defaultdict(list)
    for r in rs:
        by[r["paper"]].append(r)
    out = {}
    for adj in ("unadjusted", "holm"):
        sig = {p: [(x["fisher_p"] if adj == "unadjusted" else x[holm_key]) < 0.05 for x in v] for p, v in by.items()}
        out[adj] = dict(papers=len(sig),
                        at_least_one=frac(any(s) for s in sig.values()),
                        majority=frac(sum(s) > len(s) / 2 for s in sig.values()),
                        all=frac(all(s) for s in sig.values()))
    return out


A4 = {
    "primary_all": paper_level(prim, "holm_p_primary"),
    "primary_B": paper_level([r for r in prim if r["kind"] == "B"], "holm_p_primary"),
    "primary_A": paper_level([r for r in prim if r["kind"] == "A"], "holm_p_primary"),
}
log("A4 done")

# ------------------------------------------------------------------ A1 trial counts per condition
conds = {}
for r in included:
    for c in r["comparisons"]:
        pv = p_variant(c["note"])
        if c["nP"]:
            conds[(r["id"], c["task"], "P", pv)] = c["nP"]
        if c["nX"]:
            conds[(r["id"], c["task"], c["kind"], c["baseline_name"])] = c["nX"]
nlist = list(conds.values())
paper_median_n = [float(np.median(r["n_values"])) for r in included if r["n_values"]]
A1 = dict(
    conditions=len(nlist),
    median=float(np.median(nlist)), iqr=[float(np.percentile(nlist, 25)), float(np.percentile(nlist, 75))],
    share_le_10=frac(n <= 10 for n in nlist), share_le_20=frac(n <= 20 for n in nlist),
    share_ge_50=frac(n >= 50 for n in nlist),
    papers_with_n=len(paper_median_n),
    paper_median_of_medians=float(np.median(paper_median_n)),
    min=min(nlist), max=max(nlist),
)
log("A1 done")

# ------------------------------------------------------------------ A2 reporting
fields = ["ci_or_errorbars", "sig_test", "seeds_reported", "success_defined"]
A2 = {f: frac(bool(r["reporting"][f]) for r in included) for f in fields}
A2["randomized_init_yes"] = frac(r["reporting"]["randomized_init"] == "yes" for r in included)
A2["papers"] = len(included)
A2["eligible_but_n_missing"] = sum(1 for r in included if r.get("eligible_but_n_missing"))
A2["papers_without_binary_comparison"] = sum(
    1 for r in included if not any(c["outcome"] == "success" for c in r["comparisons"]))
A2["papers_with_partial_credit_rows"] = sum(
    1 for r in included if any(c["outcome"] != "success" for c in r["comparisons"]))
log("A2 done")

# ------------------------------------------------------------------ A6 null simulation
A6 = []
for n in (5, 10, 20, 50):
    for k in (1, 3, 5):
        for p in (0.3, 0.5, 0.7):
            for m in (1, 3, 5):
                p10, p20 = S.null_sim(n, k, p, m)
                A6.append(dict(n=n, k=k, p=p, m=m, P_ge_10=p10, P_ge_20=p20))
log("A6 done")

# ------------------------------------------------------------------ A7 sequential testing
A7 = []
for pX, pP in ((0.5, 0.5), (0.5, 0.6), (0.5, 0.7), (0.5, 0.8), (0.5, 0.9)):
    used, acc, undecided = S.sprt_sim(pP, pX)
    A7.append(dict(pX=pX, pP=pP, mean_pairs=used, P_decide_for_P=acc, P_undecided=undecided))
fixed_n = S.n_fisher_exact(0.7, 0.5, nmax=400)
log("A7 done")


# ------------------------------------------------------------------ write outputs
def write_csv(path, dicts):
    if not dicts:
        return
    keys = list(dicts[0].keys())
    for d in dicts[1:]:
        for k in d:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for d in dicts:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in d.items()})


write_csv(os.path.join(OUT, "comparisons.csv"), rows)
write_csv(os.path.join(OUT, "conditions.csv"),
          [dict(paper=k[0], task=k[1], arm=k[2], label=k[3], n=v) for k, v in conds.items()])
paper_rows = []
for r in included:
    rs = [x for x in prim if x["paper"] == r["id"]]
    paper_rows.append(dict(paper=r["id"], title=r["title"], signal=r["signal"], **r["reporting"],
                           binary_primary=len(rs), resolved_unadj=sum(x["fisher_p"] < 0.05 for x in rs),
                           resolved_holm=sum(x["holm_p_primary"] < 0.05 for x in rs),
                           n_values=" ".join(map(str, r["n_values"]))))
write_csv(os.path.join(OUT, "papers.csv"), paper_rows)
write_csv(os.path.join(OUT, "null_sim.csv"), A6)
write_csv(os.path.join(OUT, "sprt.csv"), A7)

summary = dict(records=len(records), included=len(included), binary_rows=len(rows), primary_rows=len(prim),
               papers_with_primary=len({r["paper"] for r in prim}),
               A1=A1, A2=A2, A3=A3, A4=A4, A6_grid_size=len(A6),
               A6_headline={f"n{d['n']}_k{d['k']}_p{d['p']}_m{d['m']}": d for d in A6
                            if d["p"] == 0.5},
               A7=A7, A7_fixed_n_fisher_0p7_vs_0p5=fixed_n)
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=str)

# LaTeX macros: \Audit<Name>{value}; percentages rounded to whole numbers
M = {}


def pct(x):
    return f"{100 * x:.0f}\\%"


def num(x, d=0):
    return f"{x:.{d}f}"


M["Records"] = len(records)
M["Included"] = len(included)
M["Excluded"] = len(records) - len(included)
M["BinaryRows"] = len(rows)
M["PrimaryRows"] = len(prim)
M["PrimaryRowsB"] = A3["primary_B"]["n"]
M["PrimaryRowsA"] = A3["primary_A"]["n"]
M["PapersWithComparisons"] = summary["papers_with_primary"]
M["Conditions"] = A1["conditions"]
M["MedianN"] = num(A1["median"])
M["NQOne"], M["NQThree"] = num(A1["iqr"][0]), num(A1["iqr"][1])
M["ShareNLeTen"] = pct(A1["share_le_10"])
M["ShareNLeTwenty"] = pct(A1["share_le_20"])
M["ShareNGeFifty"] = pct(A1["share_ge_50"])
for f, name in (("ci_or_errorbars", "RepCI"), ("sig_test", "RepTest"), ("seeds_reported", "RepSeeds"),
                ("success_defined", "RepSuccessDef"), ("randomized_init_yes", "RepRandInit")):
    M[name] = pct(A2[f])
for key, tag in (("primary_all", ""), ("primary_B", "B"), ("primary_A", "A")):
    s = A3[key]
    M[f"Share{tag}PBetter"] = pct(s["p_gt"])
    M[f"Share{tag}CIExcl"] = pct(s["ci_excludes_0"])
    M[f"Share{tag}FisherSig"] = pct(s["fisher_sig"])
    M[f"Share{tag}BoschlooSig"] = pct(s["boschloo_sig"])
    M[f"MedianDiff{tag}"] = num(s["median_diff_pts"])
    M[f"MedianReqN{tag}"] = num(s["n_required_median"])
    M[f"ShareAdequateN{tag}"] = pct(s["share_reported_n_adequate"])
    M[f"MedianMDD{tag}"] = num(s["mdd_median_pts"])
    for adj, at in (("unadjusted", "Unadj"), ("holm", "Holm")):
        pl = A4[key][adj]
        M[f"Papers{tag}{at}AtLeastOne"] = pct(pl["at_least_one"])
        M[f"Papers{tag}{at}Majority"] = pct(pl["majority"])
        M[f"Papers{tag}{at}All"] = pct(pl["all"])
M["SensAllRowsCIExcl"] = pct(A3["all_rows"]["ci_excludes_0"])
M["SensNoAmbCIExcl"] = pct(A3["primary_excl_ambiguous"]["ci_excludes_0"])
M["FisherBoschlooDisagree"] = A3["fisher_boschloo_disagree"]
M["ExactPowerAtArcsineN"] = num(A3["primary_all"]["exact_power_at_arcsine_n_mean"], 2)
M["ExactOverArcsineN"] = num(A3["exact_over_arcsine_n_median"], 2)
M["ExactChecked"] = A3["primary_all"]["n_exact_checked"]
M["ShareExactPowerBelowSeventy"] = pct(A3["primary_all"]["share_exact_power_below_0p7"])
M["MedianExactReqN"] = num(A3["primary_all"]["n_fisher_exact_median"])
M["ShareAdequateExactN"] = pct(A3["primary_all"]["share_reported_n_adequate_exact"])
d = {(x["n"], x["k"], x["p"], x["m"]): x for x in A6}
M["NullTenOneFiveOne"] = pct(d[(10, 1, 0.5, 1)]["P_ge_10"])
M["NullTenThreeFiveThree"] = pct(d[(10, 3, 0.5, 3)]["P_ge_10"])
M["NullTwentyOneFiveOne"] = pct(d[(20, 1, 0.5, 1)]["P_ge_10"])
M["NullTwentyThreeFiveThree"] = pct(d[(20, 3, 0.5, 3)]["P_ge_10"])
M["NullTwentyOneFiveFiveTwenty"] = pct(d[(20, 1, 0.5, 5)]["P_ge_20"])
M["SPRTPairsSeventy"] = num([x for x in A7 if x["pP"] == 0.7][0]["mean_pairs"])
M["SPRTPairsNull"] = num([x for x in A7 if x["pP"] == 0.5][0]["mean_pairs"])
M["FixedNSeventy"] = fixed_n

with open(os.path.join(OUT, "macros.tex"), "w") as fh:
    fh.write("% generated by analyze.py -- do not edit by hand\n")
    for k, v in M.items():
        fh.write(f"\\newcommand{{\\Audit{k}}}{{{v}}}\n")
log("outputs written to results/")
