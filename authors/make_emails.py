"""One ready-to-send plain-text email per included paper, plus a tracking sheet.

Usage: python3 authors/make_emails.py  ->  authors/emails/<arXiv id>.txt, authors/emails/TRACKER.csv
The corresponding author's name and address must be read from the paper's first page (arXiv PDF) and filled in.
"""
import sys
import csv, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from stats import newcombe
OUT = os.path.join(ROOT, "authors", "emails")
os.makedirs(OUT, exist_ok=True)
REPO = "https://github.com/CAN-Aidoo/trial-audit-2026"
DOI = "https://doi.org/10.5281/zenodo.23452145"
PDF = REPO + "/blob/main/paper/main.pdf"
stats = {}
for r in csv.DictReader(open(os.path.join(ROOT, "results/comparisons.csv"))):
    stats.setdefault((r["paper"], r["task"], r["kind"], r["baseline"]), r)
ROLE = {"A": "same method without the force/touch input", "B": "strongest eligible baseline"}


def kn(s, n):
    return f"{s}/{n}" if s is not None else (f"partial credit, n={n}" if n else "n not stated")


BODY = """Dear {salutation},

I am auditing how much statistical evidence backs the real-robot results in 2026 papers on force-, tactile- and current-aware manipulation. Your paper "{title}" (arXiv {id}) is one of the 58 included.

The audit is about evaluation practice across the field, not about any single paper. The main text reports results only in aggregate. An appendix table lists each included paper by arXiv ID with its number of comparisons, and the per-row data are public.

Could you check the numbers I extracted from your paper (below)? In particular:
1. the trial and success counts;
2. whether each comparator is the right one for its role.

If anything is wrong, I will correct it in the next revision and credit you by name, or anonymously if you prefer. If everything is right, no reply is needed.

Preprint: {pdf}
Data, code and protocol: {repo} (archived at {doi})

Thank you for your time, and for writing a paper clear enough to audit in this much detail.

Best regards,
Clement Aidoo
CANLABS, Ghana
clement.aidoo@canlabs.org
ORCID 0009-0005-6893-2677

------------------------------------------------------------
Rows extracted from arXiv {id}
------------------------------------------------------------
{rows}

How I coded the reporting of your real-robot results:
{reporting}
"""

rows_out = []
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "data/extract/*.json"))):
    rec = json.load(open(f))
    if not rec["include"]:
        continue
    R = []
    for i, c in enumerate(rec["comparisons"], 1):
        # CI computed from this row's own counts (a lookup keyed on task/role/baseline mixed up rows that share a key)
        if None not in (c["sP"], c["nP"], c["sX"], c["nX"]) and c["nP"] and c["nX"]:
            lo, hi = newcombe(c["sP"], c["nP"], c["sX"], c["nX"])
            ci = f"{100 * lo:+.0f} to {100 * hi:+.0f} points"
        else:
            ci = "not tested"
        flag = " (count rebuilt from a percentage)" if c["n_ambiguous"] else ""
        R.append(f"{i}. {c['task']}\n   Compared with: {c['baseline_name']} ({ROLE[c['kind']]})\n"
                 f"   Your method: {kn(c['sP'], c['nP'])}{flag}   Comparator: {kn(c['sX'], c['nX'])}\n"
                 f"   Source in paper: {c['source']}   95% CI for the difference: {ci}")
    rp = rec["reporting"]
    yes = lambda v: "yes" if v is True or v == "yes" else ("unclear" if v == "unclear" else "no")
    rep = "\n".join([f"- Interval or error bars on success: {yes(rp['ci_or_errorbars'])}",
                     f"- Any significance test: {yes(rp['sig_test'])}",
                     f"- Number of training seeds stated: {yes(rp['seeds_reported'])}",
                     f"- Explicit success criterion: {yes(rp['success_defined'])}",
                     f"- Randomised or matched initial conditions described: {yes(rp['randomized_init'])}"])
    short = rec["title"] if len(rec["title"]) <= 70 else rec["title"][:67].rstrip() + "..."
    subject = f'Please check the numbers I extracted from "{short}" (arXiv {rec["id"]})'
    body = BODY.format(salutation="[Prof./Dr. SURNAME]", title=rec["title"], id=rec["id"], pdf=PDF, repo=REPO,
                       doi=DOI, rows="\n\n".join(R) if R else "I did not extract any binary success comparisons from your paper. If it reports one that I missed, please let me know.", reporting=rep)
    assert "—" not in body and "–" not in body
    open(os.path.join(OUT, f"{rec['id']}.txt"), "w").write(f"SUBJECT: {subject}\nTO: [corresponding author email]\n\n{body}")
    rows_out.append(dict(order=n + 1, arxiv_id=rec["id"], title=rec["title"], arxiv_pdf=f"https://arxiv.org/pdf/{rec['id']}",
                         comparisons=len(rec["comparisons"]), corresponding_author="", email="", sent_date="",
                         replied="", outcome="", notes=""))
    n += 1
with open(os.path.join(OUT, "TRACKER.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
    w.writeheader(); w.writerows(rows_out)
print(f"{n} emails written to authors/emails/")
