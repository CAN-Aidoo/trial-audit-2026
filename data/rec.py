import json, os
D = os.path.join(os.path.dirname(__file__), "extract")
def C(task, kind, bn, nP, sP, nX, sX, src, note="", outcome="success", amb=False):
    return dict(task=task, outcome=outcome, kind=kind, baseline_name=bn, nP=nP, sP=sP, nX=nX, sX=sX, source=src, n_ambiguous=amb, note=note)
def W(id, title, date, inc, why, sig, rep, comps, flags, elig_n=False, nvals=None):
    d = dict(id=id, title=title, date=date, include=inc, exclude_reason=why, signal=sig,
             reporting=dict(zip(["ci_or_errorbars", "sig_test", "seeds_reported", "success_defined", "randomized_init"], rep)),
             comparisons=comps, flags=flags)
    if elig_n: d["eligible_but_n_missing"] = True
    d["n_values"] = nvals if nvals is not None else sorted({c[k] for c in comps for k in ('nP','nX') if c[k]})
    json.dump(d, open(os.path.join(D, id + ".json"), "w"), indent=1)
