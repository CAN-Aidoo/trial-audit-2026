"""README banner. Numbers are read from results/summary.json so the banner cannot drift from the paper."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(ROOT, "results/summary.json")))
a3 = s["A3"]["primary_all"]
better, resolved = a3["p_gt"], a3["ci_excludes_0"]
median_n = s["A1"]["median"]
pow20 = a3["median_power_gain20"]

BG, INK, INK2, RULE = "#f7f6f2", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, TRACK = "#2a78d6", "#eb6834", "#e9e7e1"
plt.rcParams["font.family"] = "DejaVu Sans"
fig = plt.figure(figsize=(16, 4.2), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1600); ax.set_ylim(0, 420); ax.axis("off")

ax.text(60, 330, "HOW MANY TRIALS BACK A", fontsize=15, color=INK2, fontweight="bold")
ax.text(60, 268, "Force-Aware Manipulation Claim?", fontsize=32, color=INK, fontweight="bold")
ax.text(60, 215, f"A statistical audit of {s['binary_rows']} real-robot comparisons from {s['included']} papers (2026)",
        fontsize=16, color=INK2)
ax.text(60, 150, f"Median evaluation: {median_n:.0f} trials per condition.", fontsize=16, color=INK)
ax.text(60, 118, f"Median power to detect a real 20-point gain: {pow20:.2f}.", fontsize=16, color=INK)
ax.plot([60, 1540], [72, 72], color=RULE, lw=1.5)
ax.text(60, 38, "Open data, code & protocol  ·  doi:10.5281/zenodo.23452145", fontsize=13, color=INK2)
ax.text(1540, 38, "About evaluation practice, not any paper's merit", fontsize=13, color=INK2, ha="right")

x0, w, h = 1080, 460, 30
for y, frac, col, label in ((290, better, BLUE, "Proposed method scored higher"),
                            (190, resolved, ORANGE, "Difference statistically resolved")):
    ax.text(x0, y + 44, label, fontsize=15, color=INK)
    ax.add_patch(FancyBboxPatch((x0, y), w, h, boxstyle="round,pad=0,rounding_size=6", fc=TRACK, ec="none"))
    ax.add_patch(FancyBboxPatch((x0, y), w * frac, h, boxstyle="round,pad=0,rounding_size=6", fc=col, ec="none"))
    ax.text(x0 + w * frac - 12, y + h / 2, f"{100 * frac:.0f}%", fontsize=15, color="white",
            fontweight="bold", ha="right", va="center")
ax.text(x0, 158, "95% interval for the gap excludes zero", fontsize=12, color=INK2)
fig.savefig(os.path.join(ROOT, "assets/banner.png"), facecolor=BG)
print(f"better {better:.3f} resolved {resolved:.3f} median_n {median_n} pow20 {pow20:.3f}")
