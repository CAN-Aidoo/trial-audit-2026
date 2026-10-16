"""Figures for the paper, from results/ only. Usage: python3 make_figures.py"""
import csv
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import stats as S  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "paper")
os.makedirs(OUT, exist_ok=True)

BLUE, ORANGE, VIOLET = "#2a78d6", "#eb6834", "#6250d6"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "font.family": "DejaVu Sans", "savefig.dpi": 300})


def rd(name):
    return list(csv.DictReader(open(os.path.join(R, name))))


# ---- Figure 1: trials per condition
n = [int(r["n"]) for r in rd("conditions.csv")]
fig, ax = plt.subplots(figsize=(3.4, 2.3))
edges = [0, 5.5, 10.5, 15.5, 20.5, 25.5, 30.5, 40.5, 50.5, 100.5, 250]
labels = ["≤5", "6–10", "11–15", "16–20", "21–25", "26–30", "31–40", "41–50", "51–100", ">100"]
counts, _ = np.histogram(n, bins=edges)
ax.bar(range(len(counts)), counts, color=BLUE, width=0.82)
ax.set_xticks(range(len(counts)), labels, rotation=45, ha="right")
ax.set_xlabel("Trials per condition")
ax.set_ylabel("Conditions")
ax.grid(axis="x", visible=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_n.pdf"))
plt.close(fig)

# ---- Figure 2: observed difference vs trials per arm, with the detectable-difference curve
rows = [r for r in rd("comparisons.csv") if r["primary"] == "True"]
x = np.array([int(r["n_reported_per_arm"]) for r in rows])
d = np.array([float(r["diff"]) * 100 for r in rows])
res = np.array([r["ci_excludes_0"] == "True" for r in rows])
rng = np.random.default_rng(0)
jit = x * np.exp(rng.normal(0, 0.04, len(x)))
fig, ax = plt.subplots(figsize=(3.4, 2.6))
ax.scatter(jit[~res], d[~res], s=12, color=ORANGE, alpha=0.75, linewidths=0, label="CI includes 0")
ax.scatter(jit[res], d[res], s=12, color=BLUE, alpha=0.75, linewidths=0, label="CI excludes 0")
ns = np.arange(5, 201)
mdd = [S.mdd_arcsine(0.5, k, k) * 100 for k in ns]
ax.plot(ns, mdd, color=INK, lw=1.2)
ax.axhline(0, color=INK2, lw=0.8)
ax.set_xscale("log")
ax.set_xticks([5, 10, 20, 50, 100, 200], ["5", "10", "20", "50", "100", "200"])
ax.minorticks_off()
ax.set_xlabel("Trials per arm (smaller arm)")
ax.set_ylabel("Reported gap (pts)")
ax.legend(frameon=False, fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_gap.pdf"))
plt.close(fig)

# ---- Figure 3: null simulation, chance of an apparent >= 10-point gain when methods are equal
ns_ = [5, 10, 20, 50]
sim = rd("null_sim.csv")
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for m, col in ((1, BLUE), (3, ORANGE), (5, VIOLET)):
    y = [100 * float(next(r["P_ge_10"] for r in sim if int(r["n"]) == k and int(r["k"]) == 1
                          and float(r["p"]) == 0.5 and int(r["m"]) == m)) for k in ns_]
    ax.plot(ns_, y, color=col, lw=2, marker="o", ms=4, label=f"best of {m}")
ax.set_xscale("log")
ax.set_xticks(ns_, [str(k) for k in ns_])
ax.minorticks_off()
ax.set_ylim(0, 100)
ax.set_xlim(4.5, 60)
ax.set_xlabel("Trials per arm (one task, both true rates 50%)")
ax.set_ylabel("Chance of ≥10-pt gain (%)")
ax.legend(frameon=False, fontsize=7, loc="upper right")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_null.pdf"))
plt.close(fig)
print("figures written to paper/")
