"""Compare the first extraction (data/extract) with the blinded second extraction (verify/out).

Writes verify/agreement.json (pre-adjudication agreement statistics, reported in the paper)
and verify/discrepancies.csv (every disagreement, for adjudication against the source).
"""
import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "verify")
first = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "data/extract/*.json"))}

screen, rows, missing = {}, {}, []
for f in sorted(glob.glob(os.path.join(V, "out", "batch_*_screen.json"))):
    for s in json.load(open(f)):
        screen[s["id"]] = s
for f in sorted(glob.glob(os.path.join(V, "out", "batch_*_rows.json"))):
    for r in json.load(open(f)):
        if "missing_rows" in r:
            if r["missing_rows"]:
                missing.append(r)
            continue
        rows[(r["id"], int(r["row"]))] = r

disc = []


def add(pid, row, field, first_v, second_v, extra=""):
    disc.append(dict(paper=pid, row=row, field=field, first=first_v, second=second_v, detail=extra))


# ---- screening
pairs = [(first[p]["include"], bool(s["include"])) for p, s in screen.items() if p in first]
agree = sum(a == b for a, b in pairs)
n = len(pairs)
pa = agree / n if n else float("nan")
p1 = sum(a for a, _ in pairs) / n
p2 = sum(b for _, b in pairs) / n
pe = p1 * p2 + (1 - p1) * (1 - p2)
kappa = (pa - pe) / (1 - pe) if pe < 1 else float("nan")
for p, s in screen.items():
    if p in first and first[p]["include"] != bool(s["include"]):
        add(p, "", "include", f"{first[p]['include']} ({first[p]['exclude_reason']})",
            f"{s['include']} ({s.get('reason')})")

# ---- reporting fields (papers both include)
rep_fields = ["ci_or_errorbars", "sig_test", "seeds_reported", "success_defined", "randomized_init"]
rep_agree = {f: [0, 0] for f in rep_fields}
for p, s in screen.items():
    if p in first and first[p]["include"] and s.get("include") and s.get("reporting"):
        for f in rep_fields:
            a, b = first[p]["reporting"][f], s["reporting"].get(f)
            if f != "randomized_init":
                a, b = bool(a), bool(b)
            rep_agree[f][1] += 1
            if a == b:
                rep_agree[f][0] += 1
            else:
                add(p, "", "reporting." + f, a, b)

# ---- numeric rows
num = dict(rows=0, exact=0, binary_rows=0, binary_exact=0, outcome_agree=0, not_found=0,
           b_rows=0, b_flagged=0, a_rows=0, a_flagged=0)
for pid, rec in first.items():
    if not rec["include"]:
        continue
    for i, c in enumerate(rec["comparisons"]):
        v = rows.get((pid, i))
        if v is None:
            continue
        num["rows"] += 1
        same_outcome = (c["outcome"] == "success") == (v.get("outcome") == "success")
        num["outcome_agree"] += same_outcome
        if not same_outcome:
            add(pid, i, "outcome", c["outcome"], v.get("outcome"), c["task"])
        vals1 = (c["nP"], c["sP"], c["nX"], c["sX"])
        vals2 = tuple(v.get(k) for k in ("nP", "sP", "nX", "sX"))
        if all(x is None for x in vals2):
            num["not_found"] += 1
        match = vals1 == vals2 or (c["outcome"] != "success" and (vals1[0], vals1[2]) == (vals2[0], vals2[2]))
        num["exact"] += match
        if c["outcome"] == "success":
            num["binary_rows"] += 1
            num["binary_exact"] += vals1 == vals2
        if not match:
            add(pid, i, "numbers", vals1, vals2, f"{c['task']} | {c['kind']} vs {c['baseline_name']} | "
                f"src1 {c['source']} | src2 {v.get('source')} | {v.get('comment', '')}")
        if c["kind"] == "B":
            num["b_rows"] += 1
            if v.get("b_ok") is False:
                num["b_flagged"] += 1
                add(pid, i, "B choice", c["baseline_name"], v.get("b_should_be"), f"{c['task']} | {v.get('comment', '')}")
        if c["kind"] == "A":
            num["a_rows"] += 1
            if v.get("a_ok") is False:
                num["a_flagged"] += 1
                add(pid, i, "A choice", c["baseline_name"], "not a no-signal ablation", f"{c['task']} | {v.get('comment', '')}")

for m in missing:
    add(m["id"], "", "missing_rows", "", json.dumps(m["missing_rows"])[:500])

out = dict(screened=n, include_agree=agree, include_kappa=kappa,
           reporting_agreement={f: (a / t if t else None, t) for f, (a, t) in rep_agree.items()},
           numeric=num, papers_with_missing_rows=len(missing), discrepancies=len(disc))
json.dump(out, open(os.path.join(V, "agreement.json"), "w"), indent=1)
with open(os.path.join(V, "discrepancies.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["paper", "row", "field", "first", "second", "detail"])
    w.writeheader()
    w.writerows(disc)
print(json.dumps(out, indent=1))
