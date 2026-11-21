"""Hand-computed checks for src/models/evaluate.py (no data files needed)."""
import math

import numpy as np
import pandas as pd
import pytest

from src.models.evaluate import evaluate_quantiles, pinball, results_table

# y = [100, 200, 400]; p10 = [90, 150, 300]; p50 = [100, 100, 400]; p90 = [110, 250, 390]
Y = [100, 200, 400]
P10, P50, P90 = [90, 150, 300], [100, 100, 400], [110, 250, 390]


def test_evaluate_quantiles_by_hand():
    m = evaluate_quantiles(Y, P10, P50, P90)
    assert m["n"] == 3
    # |log y - log p50| = [0, ln 2, 0]  ->  ln 2 / 3
    assert m["mae_log"] == pytest.approx(math.log(2) / 3)
    # tau=0.5: d = y - p50 = [0, 100, 0] -> 0.5 * 100 / 3
    assert m["pinball50"] == pytest.approx(50 / 3)
    # tau=0.1: d = y - p10 = [10, 50, 100] (all under-predictions) -> 0.1 * d = [1, 5, 10] -> 16/3
    assert m["pinball10"] == pytest.approx(16 / 3)
    # tau=0.9: d = y - p90 = [-10, -50, 10] -> [0.1*10, 0.1*50, 0.9*10] = [1, 5, 9] -> 5
    assert m["pinball90"] == pytest.approx(5.0)
    # 100 in [90,110], 200 in [150,250], 400 > 390
    assert m["cov80"] == pytest.approx(2 / 3)
    assert m["below_p10"] == 0.0
    assert m["above_p90"] == pytest.approx(1 / 3)


def test_pinball_direction():
    # At tau=0.9 under-predicting is the expensive mistake: 0.9*10 = 9 vs 0.1*10 = 1
    assert pinball([100], [90], 0.9) == pytest.approx(9.0)
    assert pinball([100], [110], 0.9) == pytest.approx(1.0)


def test_results_table_counts_drops_and_aligns_by_index():
    df = pd.DataFrame({"source": ["lca", "lca", "postings", "postings"],
                       "split": ["train"] * 4,
                       "annual_wage": [100.0, 200.0, 100.0, 400.0]},
                      index=[10, 11, 12, 13])
    # Deliberately shuffled index: results must not depend on row order
    pred = pd.DataFrame({"p10": [50.0, 90.0, 90.0, np.nan],
                         "p50": [200.0, 100.0, 100.0, 400.0],
                         "p90": [300.0, 110.0, 110.0, 500.0]},
                        index=[11, 10, 12, 13])
    t = results_table(df, {"baseline": pred}).set_index("source")
    assert t.loc["lca", "n"] == 2 and t.loc["lca", "n_dropped"] == 0
    assert t.loc["postings", "n"] == 1 and t.loc["postings", "n_dropped"] == 1
    assert t.loc["lca", "mae_log"] == pytest.approx(0.0)  # aligned by index: perfect P50s
    assert t["small_n"].all()


def test_results_table_rejects_duplicate_index():
    df = pd.DataFrame({"source": ["lca"] * 2, "split": ["train"] * 2, "annual_wage": [1.0, 2.0]},
                      index=[0, 0])
    with pytest.raises(ValueError):
        results_table(df, {"m": pd.DataFrame({"p10": [1.0], "p50": [1.0], "p90": [1.0]})})


def test_row_losses_average_to_evaluate_quantiles():
    from src.models.evaluate import row_losses
    pred = pd.DataFrame({"p10": P10, "p50": P50, "p90": P90}, dtype=float)
    means = row_losses(Y, pred).mean()
    m = evaluate_quantiles(Y, P10, P50, P90)
    for k in ("mae_log", "pinball10", "pinball50", "pinball90", "cov80"):
        assert means[k] == pytest.approx(m[k])


def test_cluster_bootstrap_ci():
    from src.models.evaluate import cluster_bootstrap_ci
    # constant values: zero-width interval at the constant
    assert cluster_bootstrap_ci([2.0] * 10, list("aabbccddee")) == pytest.approx((2.0, 2.0, 2.0))
    # clear positive difference: CI excludes 0 and contains the mean
    rng = np.random.default_rng(1)
    v = 1.0 + rng.normal(0, 1, 2000)
    mean, lo, hi = cluster_bootstrap_ci(v, np.arange(2000) // 4, n_boot=500)
    assert 0 < lo < mean < hi
    # one dominant cluster widens the interval vs the same data split into many clusters
    vals = np.r_[np.ones(500), np.zeros(500)]
    one_big = np.r_[np.zeros(500), np.arange(1, 501)]  # the 500 ones all belong to one company
    _, lo1, hi1 = cluster_bootstrap_ci(vals, one_big, n_boot=500)
    _, lo2, hi2 = cluster_bootstrap_ci(vals, np.arange(1000), n_boot=500)
    assert (hi1 - lo1) > 3 * (hi2 - lo2)
