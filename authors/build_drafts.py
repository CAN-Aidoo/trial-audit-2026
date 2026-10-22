"""Merge verified contacts with the per-paper emails into one draft per recipient (papers sharing a contact are combined)."""
import json, re, os, collections, sys
SC = sys.argv[1]
EM = "/home/claude/audit/authors/emails"
R = []
for i in range(6): R += json.load(open(f"{SC}/result{i}.json"))
by = {r["arxiv_id"]: r for r in R}
by["2602.22088"].update(email="shiquan.wang@flexiv.com", email_source="FP2 project page (same person, batch 5)", title_prefix="")
groups = collections.OrderedDict()
for r in R:
    if r["email"]:
        groups.setdefault(r["email"].lower(), []).append(r)

def parts(aid):
    t = open(f"{EM}/{aid}.txt").read()
    subj = t.split("\n", 1)[0].replace("SUBJECT: ", "")
    body = t[t.index("Dear "):]
    i = body.index("-" * 60)
    return subj, body[:i], body[i:]

def salutation(r):
    sur = r["name"].split()[-1]
    return f"{r['title_prefix']} {sur}" if r["title_prefix"] else r["name"]

drafts = []
for email, rs in groups.items():
    r0 = rs[0]
    subj, head, rows = parts(r0["arxiv_id"])
    head = head.replace("[Prof./Dr. SURNAME]", salutation(r0))
    if len(rs) > 1:
        titles = [json.load(open(f"/home/claude/audit/data/extract/{x['arxiv_id']}.json"))["title"] for x in rs]
        ids = [x["arxiv_id"] for x in rs]
        head = re.sub(r'Your paper ".*?" \(arXiv [0-9.]+\) is one of the 58 included\.',
                      "Two of your papers are among the 58 included: " + " and ".join(f'"{t}" (arXiv {i})' for t, i in zip(titles, ids)) + ".",
                      head, flags=re.S)
        head = head.replace("the numbers I extracted from your paper (below)", "the numbers I extracted from these papers (below)")
        head = head.replace("for writing a paper clear enough", "for writing papers clear enough")
        subj = f"Please check the numbers I extracted from two of your papers (arXiv {ids[0]}, {ids[1]})"
        rows = "".join(parts(x["arxiv_id"])[2] + "\n" for x in rs).rstrip() + "\n"
    body = head + rows
    assert "[Prof./Dr." not in body and "—" not in body
    drafts.append(dict(to=r0["email"], name=r0["name"], papers=[x["arxiv_id"] for x in rs], subject=subj, body=body))
json.dump(drafts, open(f"{SC}/drafts.json", "w"), indent=1)
print(len(drafts), "drafts;", sum(len(d["papers"]) for d in drafts), "papers")
print("no email:", [r["arxiv_id"] for r in R if not r["email"]])
