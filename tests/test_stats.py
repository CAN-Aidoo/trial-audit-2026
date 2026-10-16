"""Checks of stats.py against published values and independent computations. Run: python3 -m pytest -q tests"""
import math
import os
import sys

import numpy as np
from scipy import stats as ss

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import stats as S  # noqa: E402


def close(a, b, tol=5e-4):
    return abs(a - b) < tol


def test_wilson_known():
    # 0/10: upper bound 0.2775 (Newcombe 1998, Table I); 81/263 -> 0.2553-0.3662 (Newcombe example)
    lo, hi = S.wilson(0, 10)
    assert lo == 0 and close(hi, 0.2775)
    lo, hi = S.wilson(81, 263)
    assert close(lo, 0.2553) and close(hi, 0.3662)


def test_newcombe_published_example():
    # Newcombe (1998) Stat Med 17:873, example (a): 56/70 vs 48/80 -> method 10: 0.0524 to 0.3339
    lo, hi = S.newcombe(56, 70, 48, 80)
    assert close(lo, 0.0524) and close(hi, 0.3339)


def test_fisher_matches_scipy_and_region():
    n = 12
    R = S.fisher_reject_region(n)
    for x1 in range(n + 1):
        for x2 in range(n + 1):
            p = ss.fisher_exact([[x1, n - x1], [x2, n - x2]])[1]
            assert R[x1, x2] == (p <= 0.05)


def test_exact_power_vs_monte_carlo():
    rng = np.random.default_rng(1)
    n, p1, p2 = 30, 0.8, 0.45
    pw = S.fisher_power_exact(p1, p2, n)
    x1 = rng.binomial(n, p1, 20000)
    x2 = rng.binomial(n, p2, 20000)
    R = S.fisher_reject_region(n)
    mc = R[x1, x2].mean()
    assert abs(pw - mc) < 0.015


def test_holm():
    adj = S.holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_arcsine_n_textbook():
    # h = 2asin(sqrt .65) - 2asin(sqrt .45) = 1.8755 - 1.4706 = 0.4049 (hand computation);
    # n = 2 * ((1.95996 + 0.84162) / 0.4049)^2 = 95.8 -> 96 per arm
    assert close(abs(S.cohen_h(0.65, 0.45)), 0.4049, 1e-3)
    assert S.n_arcsine(0.65, 0.45) == 96


def test_mdd_inverts_n():
    n = S.n_arcsine(0.5, 0.8)
    d = S.mdd_arcsine(0.5, n, n)
    assert d <= 0.3 + 1e-9 and d > 0.27


def test_null_sim_symmetry():
    p10, p20 = S.null_sim(10, 1, 0.5, 1, reps=50000)
    # exact: P(X - Y >= 1) for two Bin(10, .5)
    pmf = ss.binom.pmf(np.arange(11), 10, 0.5)
    exact = sum(pmf[i] * pmf[j] for i in range(11) for j in range(11) if i - j >= 1)
    assert abs(p10 - exact) < 0.01
    assert p20 < p10


def test_sprt_error_rates():
    _, acc0, _ = S.sprt_sim(0.5, 0.5, reps=20000)
    _, acc1, _ = S.sprt_sim(0.7, 0.5, reps=20000)
    assert acc0 < 0.035          # nominal 0.025 (Wald bound is approximate)
    assert acc1 > 0.75           # nominal 0.80
