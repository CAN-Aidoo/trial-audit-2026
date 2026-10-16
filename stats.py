"""Statistical helpers for the audit (protocol v1.0, deviations D1-D7).

Everything here is deterministic except the explicitly seeded simulations.
"""
import math
from functools import lru_cache

import numpy as np
from scipy import stats

Z975 = stats.norm.ppf(0.975)   # two-sided alpha = 0.05
Z80 = stats.norm.ppf(0.80)     # power 0.80


# ---------------------------------------------------------------- intervals
def wilson(k, n, z=Z975):
    """Wilson score interval for k successes in n trials."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe(k1, n1, k2, n2, z=Z975):
    """Newcombe (1998) method 10: hybrid score CI for p1 - p2, no continuity correction."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (lo, hi)


# ---------------------------------------------------------------- tests
def fisher_p(k1, n1, k2, n2):
    return stats.fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="two-sided")[1]


def boschloo_p(k1, n1, k2, n2):
    if (k1 + k2 == 0) or (k1 + k2 == n1 + n2):
        return 1.0
    return stats.boschloo_exact([[k1, k2], [n1 - k1, n2 - k2]], alternative="two-sided", n=32).pvalue


def holm(pvals):
    """Holm step-down adjusted p-values."""
    p = np.asarray(pvals, float)
    m = len(p)
    if m == 0:
        return p
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


# ---------------------------------------------------------------- power (arcsine)
def cohen_h(p1, p2):
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def n_arcsine(p1, p2, alpha=0.05, power=0.80):
    """Trials per arm (equal arms) for a two-sided test, arcsine approximation."""
    h = abs(cohen_h(p1, p2))
    if h == 0:
        return math.inf
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return math.ceil(2 * (z / h) ** 2)


def mdd_arcsine(p_base, n1, n2, alpha=0.05, power=0.80):
    """Smallest improvement over p_base detectable with given power at arm sizes n1 (P), n2 (baseline).
    Returns nan if even p = 1 is not enough."""
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    h = z * math.sqrt(1 / n1 + 1 / n2)
    a = math.asin(math.sqrt(p_base)) + h / 2
    if a > math.pi / 2:
        return float("nan")
    return math.sin(a) ** 2 - p_base


# ---------------------------------------------------------------- exact Fisher power by enumeration
@lru_cache(maxsize=None)
def fisher_reject_region(n, alpha=0.05):
    """Boolean (n+1)x(n+1) array R[x1, x2]: two-sided Fisher test rejects for x1/n vs x2/n."""
    R = np.zeros((n + 1, n + 1), bool)
    for t in range(0, 2 * n + 1):
        lo, hi = max(0, t - n), min(n, t)
        x1 = np.arange(lo, hi + 1)
        pmf = stats.hypergeom.pmf(x1, 2 * n, n, t)   # x1 ~ successes in arm 1 given total t
        srt = np.sort(pmf)
        csum = np.cumsum(srt)
        # p-value = sum of pmf values <= observed (relative tolerance as in scipy)
        idx = np.searchsorted(srt, pmf * (1 + 1e-7), side="right") - 1
        pv = csum[idx]
        R[x1, t - x1] = pv <= alpha
    return R


def fisher_power_exact(p1, p2, n, alpha=0.05):
    R = fisher_reject_region(n, alpha)
    b1 = stats.binom.pmf(np.arange(n + 1), n, p1)
    b2 = stats.binom.pmf(np.arange(n + 1), n, p2)
    return float(b1 @ R @ b2)


def n_fisher_exact(p1, p2, alpha=0.05, power=0.80, nmax=600):
    """Smallest equal-arm n (searched upward from a lower bound) whose exact Fisher power >= target.
    Returns inf if not reached by nmax."""
    if p1 == p2:
        return math.inf
    start = max(2, int(0.7 * n_arcsine(p1, p2, alpha, power)))
    if start > nmax:
        return math.inf
    for n in range(start, nmax + 1):
        if fisher_power_exact(p1, p2, n, alpha) >= power:
            return n
    return math.inf


# ---------------------------------------------------------------- A6 null simulation
def null_sim(n, k, p, m, reps=200_000, seed=20261016):
    """Both methods have true rate p. Each of m proposed variants and one baseline run n trials on each
    of k tasks. Reported improvement = max over variants of mean-over-tasks (variant - baseline).
    Returns P(improvement >= 10 pts), P(>= 20 pts)."""
    rng = np.random.default_rng(seed)
    base = rng.binomial(n, p, size=(reps, k)) / n
    var = rng.binomial(n, p, size=(reps, m, k)) / n
    imp = (var - base[:, None, :]).mean(axis=2).max(axis=1) * 100
    return float((imp >= 10 - 1e-9).mean()), float((imp >= 20 - 1e-9).mean())


# ---------------------------------------------------------------- A7 SPRT on discordant pairs
def sprt_sim(pP, pX, design=(0.7, 0.5), alpha=0.025, beta=0.20, max_pairs=500, reps=20_000, seed=20261016):
    """Alternate one P and one X trial per pair. Only discordant pairs are informative; under H0 a
    discordant pair favours P with prob 0.5, under H1 with theta1 from the design rates.
    Returns (mean pairs used, P(decide for P), P(no decision by max_pairs))."""
    d1, d0 = design
    theta1 = d1 * (1 - d0) / (d1 * (1 - d0) + d0 * (1 - d1))
    A, B = math.log((1 - beta) / alpha), math.log(beta / (1 - alpha))
    up, down = math.log(theta1 / 0.5), math.log((1 - theta1) / 0.5)
    rng = np.random.default_rng(seed)
    a = rng.random((reps, max_pairs)) < pP
    b = rng.random((reps, max_pairs)) < pX
    step = np.where(a & ~b, up, np.where(~a & b, down, 0.0))
    llr = np.cumsum(step, axis=1)
    hitA = llr >= A
    hitB = llr <= B
    firstA = np.where(hitA.any(1), hitA.argmax(1), max_pairs)
    firstB = np.where(hitB.any(1), hitB.argmax(1), max_pairs)
    stop = np.minimum(firstA, firstB)
    decided = stop < max_pairs
    used = np.where(decided, stop + 1, max_pairs)
    accept_P = decided & (firstA < firstB)
    return float(used.mean()), float(accept_P.mean()), float((~decided).mean())
