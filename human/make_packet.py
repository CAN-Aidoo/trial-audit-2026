"""Draw the seeded 20% sample for the blinded human re-check and write blank coding sheets.

Usage: python3 human/make_packet.py   (refuses to overwrite an existing sample)
Writes human/sample.json, human/1_screening.csv, human/2_rows.csv. The sheets contain no trial counts,
successes or decisions from the AI extraction.
"""
import csv
import glob
import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(ROOT, "human")
SEED = 20261016
if os.path.exists(os.path.join(H, "sample.json")):
    raise SystemExit("sample.json exists; the sample is fixed once drawn")

recs = sorted((json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "data/extract/*.json"))), key=lambda r: r["id"])
inc = [r["id"] for r in recs if r["include"]]
exc = [r["id"] for r in recs if not r["include"]]
rng = random.Random(SEED)
s_inc = sorted(rng.sample(inc, math.ceil(0.2 * len(inc))))
s_exc = sorted(rng.sample(exc, math.ceil(0.2 * len(exc))))
order = s_inc + s_exc
random.Random(SEED + 1).shuffle(order)          # mix so inclusion status is not given away by position
json.dump(dict(seed=SEED, included_sampled=s_inc, excluded_sampled=s_exc, order=order), open(os.path.join(H, "sample.json"), "w"), indent=1)

byid = {r["id"]: r for r in recs}
with open(os.path.join(H, "1_screening.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "title", "link", "include (Y/N)", "reason (I1/I2/I3 failed, or meets I1-I3)",
                "signal (force/torque/tactile/current/mixed)", "ci_or_errorbars (Y/N)", "sig_test (Y/N)",
                "seeds_reported (Y/N)", "success_defined (Y/N)", "randomized_init (yes/no/unclear)",
                "eligible_but_n_missing (Y/N)", "minutes spent", "notes"])
    for pid in order:
        w.writerow([pid, byid[pid]["title"], f"https://arxiv.org/abs/{pid}"] + [""] * 11)

with open(os.path.join(H, "2_rows.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "row", "task", "kind", "comparator", "P variant (if any)",
                "nP", "sP", "nX", "sX", "outcome (success/partial)", "n_ambiguous (Y/N)", "source (table/fig, page)",
                "comparator OK? (Y/N)", "should be (if not OK)", "notes"])
    for pid in order:
        if pid not in s_inc:
            continue
        for i, c in enumerate(byid[pid]["comparisons"]):
            pv = c["note"].split(";")[0][4:].strip() if c["note"].startswith("P = ") else ""
            w.writerow([pid, i, c["task"], c["kind"], c["baseline_name"], pv] + [""] * 10)
print(f"sampled {len(s_inc)} included + {len(s_exc)} excluded papers")
