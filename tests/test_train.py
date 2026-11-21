"""Checks for Stage 1 features and QuantReg training (no data files needed)."""
import numpy as np
import pandas as pd
import pytest

from src.models.features import LINEAR_COLUMNS, REFERENCE_SOC, linear_features
from src.models.train import fit_quantreg, fix_crossing, predict_quantreg


def test_fix_crossing_sorts_and_counts():
    pred = pd.DataFrame({"p10": [1.0, 5.0, 1.0], "p50": [2.0, 4.0, 3.0], "p90": [3.0, 6.0, 2.0]},
                        index=[7, 8, 9])
    fixed, crossed = fix_crossing(pred)
    assert crossed == 2  # row 8 (p10 > p50) and row 9 (p50 > p90)
    assert fixed.loc[8].tolist() == [4.0, 5.0, 6.0]
    assert fixed.loc[9].tolist() == [1.0, 2.0, 3.0]
    assert list(fixed.index) == [7, 8, 9]


def test_quantreg_recovers_known_quantiles():
    # y = 1 + 2x + e, e ~ Uniform(-1, 1): true tau-quantile line is 1 + 2x + (2*tau - 1)
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1, 4000)
    y = 1 + 2 * x + rng.uniform(-1, 1, 4000)
    X = pd.DataFrame({"const": 1.0, "x": x})
    models = fit_quantreg(X, pd.Series(y))
    for tau in (0.1, 0.5, 0.9):
        assert models[tau]["const"] == pytest.approx(1 + (2 * tau - 1), abs=0.08)
        assert models[tau]["x"] == pytest.approx(2.0, abs=0.12)


def test_predict_quantreg_exponentiates_log_predictions():
    X = pd.DataFrame({"const": [1.0, 1.0], "x": [0.0, 1.0]}, index=["a", "b"])
    models = {t: pd.Series({"const": np.log(100.0), "x": np.log(2.0)}) for t in (0.1, 0.5, 0.9)}
    pred = predict_quantreg(models, X)
    assert pred.loc["a", "p50"] == pytest.approx(100.0)
    assert pred.loc["b", "p90"] == pytest.approx(200.0)


def test_linear_features_columns_and_soc_reference():
    df = pd.DataFrame({"soc_code": [REFERENCE_SOC, "15-2051", "99-9999"],
                       "metro": ["41940", None, "14460"]})
    bls = pd.DataFrame({"p10": [80e3, 90e3, 70e3], "p50": [100e3, 120e3, 90e3],
                        "p90": [160e3, 180e3, 140e3]})
    X = linear_features(df, bls)
    assert list(X.columns) == LINEAR_COLUMNS
    soc_cols = [c for c in X.columns if c.startswith("soc_")]
    assert X.loc[0, soc_cols].sum() == 0               # reference occupation
    assert X.loc[1, "soc_15-2051"] == 1 and X.loc[1, "metro_missing"] == 1
    assert X.loc[2, soc_cols].sum() == 0               # out-of-scope SOC -> reference
    assert X.loc[0, "log_bls_spread"] == pytest.approx(np.log(160e3 / 80e3))


def test_no_predict_time_unavailable_features():
    # predict() never receives these; using them would be leakage or a train/serve mismatch
    banned = ("wage_level", "source", "employer", "year", "split", "fold")
    assert not [c for c in LINEAR_COLUMNS if any(b in c for b in banned)]
