"""Evaluation metrics shared by the baseline and the quantile models. Owner: Sophak."""
import numpy as np


def mae_log(y, p) -> float:
    """Mean absolute error on log wages (scale-free: 0.10 ~ 10% typical error)."""
    return float(np.mean(np.abs(np.log(np.asarray(y, float)) - np.log(np.asarray(p, float)))))


def pinball(y, q, tau: float) -> float:
    """Pinball (quantile) loss of prediction q at quantile tau, in the units of y."""
    d = np.asarray(y, float) - np.asarray(q, float)
    return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))


def coverage(y, lo, hi) -> float:
    """Share of y inside [lo, hi]; a calibrated P10-P90 interval should give ~0.80."""
    y = np.asarray(y, float)
    return float(np.mean((y >= np.asarray(lo, float)) & (y <= np.asarray(hi, float))))
