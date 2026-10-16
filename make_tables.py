"""Generated LaTeX tables for the paper. Usage: python3 make_tables.py (after analyze.py)."""
import csv
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(ROOT, "paper")
os.makedirs(P, exist_ok=True)
recs = sorted((json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "data/extract/*.json"))),
              key=lambda r: r["id"])
papers = {r["paper"]: r for r in csv.DictReader(open(os.path.join(ROOT, "results/papers.csv")))}


def tex(s):
    return re.sub(r"([&%#_$])", r"\\\1", s)


def short_reason(r):
    why = (r.get("exclude_reason") or "").strip()
    m = re.match(r"(I\d(?: \(D\d\))?)", why)
    if m:
        return m.group(1)
    for key, lab in (("date", "date (D1)"), ("survey", "survey"), ("simulation", "I2 (sim.)"), ("hardware", "hardware only")):
        if key in why.lower():
            return lab
    return tex(why[:22])


lines = [r"\begin{longtable}{@{}llrrrl@{}}",
         r"\caption{All screened papers. Binary = primary binary comparisons; resolved = Fisher $p<0.05$ after "
         r"Holm correction within the paper. Per-row data, sources and coder notes are in the released "
         r"data.}\label{tab:papers}\\",
         r"\toprule arXiv ID & Signal & Binary & Resolved & Median $n$ & Status \\ \midrule \endfirsthead",
         r"\toprule arXiv ID & Signal & Binary & Resolved & Median $n$ & Status \\ \midrule \endhead",
         r"\bottomrule \endfoot"]
for r in recs:
    if r["include"]:
        p = papers.get(r["id"], {})
        nv = r["n_values"]
        med = sorted(nv)[len(nv) // 2] if nv else "--"
        lines.append(f"{r['id']} & {tex(r['signal'])} & {p.get('binary_primary', 0)} & "
                     f"{p.get('resolved_holm', 0)} & {med} & included \\\\")
    else:
        lines.append(f"{r['id']} & {tex(r['signal'] or '--')} & -- & -- & -- & excluded: {short_reason(r)} \\\\")
lines.append(r"\end{longtable}")
open(os.path.join(P, "tab_papers.tex"), "w").write("\n".join(lines) + "\n")

# A6 excerpt table
sim = list(csv.DictReader(open(os.path.join(ROOT, "results/null_sim.csv"))))
rows = [r"\begin{tabular}{@{}rr" + "rrr" * 2 + r"@{}}", r"\toprule",
        r" & & \multicolumn{3}{c}{$\Pr(\text{gain}\ge 10)$} & \multicolumn{3}{c}{$\Pr(\text{gain}\ge 20)$}\\",
        r"\cmidrule(lr){3-5}\cmidrule(l){6-8}",
        r"$n$ & $k$ & $m{=}1$ & $m{=}3$ & $m{=}5$ & $m{=}1$ & $m{=}3$ & $m{=}5$\\ \midrule"]
for n in (5, 10, 20, 50):
    for k in (1, 3, 5):
        cells = []
        for col in ("P_ge_10", "P_ge_20"):
            for m in (1, 3, 5):
                v = next(float(r[col]) for r in sim if int(r["n"]) == n and int(r["k"]) == k
                         and float(r["p"]) == 0.5 and int(r["m"]) == m)
                cells.append(f"{100 * v:.0f}")
        rows.append(f"{n} & {k} & " + " & ".join(cells) + r"\\")
    if n != 50:
        rows.append(r"\addlinespace")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(P, "tab_null.tex"), "w").write("\n".join(rows) + "\n")

# A7 table
sp = list(csv.DictReader(open(os.path.join(ROOT, "results/sprt.csv"))))
rows = [r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
        r"True rates ($p_X$, $p_P$) & Mean trials per arm & $\Pr$(decide for P) & $\Pr$(no decision)\\ \midrule"]
for r in sp:
    rows.append(f"({float(r['pX']):.1f}, {float(r['pP']):.1f}) & {float(r['mean_pairs']):.0f} & "
                f"{float(r['P_decide_for_P']):.3f} & {float(r['P_undecided']):.3f}\\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(P, "tab_sprt.tex"), "w").write("\n".join(rows) + "\n")
# A5 design grid (D9)
dg = list(csv.DictReader(open(os.path.join(ROOT, "results/design_grid.csv"))))
rows = [r"\begin{tabular}{@{}rrrrr@{}}", r"\toprule",
        r"Comparator rate & Target gain & Arcsine $n$ & Exact power at arcsine $n$ & Exact $n$\\ \midrule"]
for r in dg:
    rows.append(f"{float(r['p_base']):.1f} & +{100 * float(r['gain']):.0f} pts & {r['n_arcsine']} & "
                f"{float(r['power_exact_at_arcsine_n']):.2f} & {r['n_exact']}\\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(P, "tab_design.tex"), "w").write("\n".join(rows) + "\n")
print("tables written to paper/")
