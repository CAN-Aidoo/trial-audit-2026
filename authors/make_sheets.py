"""One confirmation sheet per included paper, for sending to its authors before the revision.

Usage: python3 authors/make_sheets.py  ->  authors/sheets/<arXiv id>.md
"""
import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "authors", "sheets")
os.makedirs(OUT, exist_ok=True)
stats = {}
for r in csv.DictReader(open(os.path.join(ROOT, "results/comparisons.csv"))):
    stats.setdefault((r["paper"], r["task"], r["kind"], r["baseline"]), r)

KIND = {"A": "same method without the force/touch input", "B": "strongest eligible baseline"}
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "data/extract/*.json"))):
    rec = json.load(open(f))
    if not rec["include"]:
        continue
    L = [f"# {rec['title']}", f"arXiv {rec['id']}", "",
         "| # | Task | Comparator (role) | Proposed method k/n | Comparator k/n | Where we read it | 95% CI for the difference (pts) |",
         "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(rec["comparisons"]):
        def kn(s, nn):
            return f"{s}/{nn}" if s is not None else (f"partial credit, n={nn}" if nn else "n not stated")
        st = stats.get((rec["id"], c["task"], c["kind"], c["baseline_name"]))
        ci = f"{100 * float(st['nc_lo']):+.0f} to {100 * float(st['nc_hi']):+.0f}" if st else "not tested"
        flag = " (count rebuilt from a percentage)" if c["n_ambiguous"] else ""
        L.append(f"| {i} | {c['task']} | {c['baseline_name']} ({KIND[c['kind']]}) | {kn(c['sP'], c['nP'])}{flag} | "
                 f"{kn(c['sX'], c['nX'])} | {c['source']} | {ci} |")
    rp = rec["reporting"]
    yes = lambda v: "yes" if v is True or v == "yes" else ("unclear" if v == "unclear" else "no")
    L += ["", "How we coded the paper's reporting of its real-robot results:",
          f"- Interval or error bars on success: {yes(rp['ci_or_errorbars'])}",
          f"- Any significance test: {yes(rp['sig_test'])}",
          f"- Number of training seeds stated: {yes(rp['seeds_reported'])}",
          f"- Explicit success criterion: {yes(rp['success_defined'])}",
          f"- Randomised or matched initial conditions described: {yes(rp['randomized_init'])}", ""]
    open(os.path.join(OUT, f"{rec['id']}.md"), "w").write("\n".join(L))
    n += 1
print(f"{n} sheets written to authors/sheets/")
