from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from scipy.stats import gaussian_kde


def robust_mad(x: np.ndarray) -> float:
    """Median absolute deviation scaled to ~1-sigma for normal."""
    x = np.asarray(x, dtype=float)
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return 1.4826 * mad if mad > 0 else float(np.std(x))


def filter_outliers_within_span(
    ages: np.ndarray,
    sigmas: np.ndarray,
    max_span_ma: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    论文思路：剔除年龄差 > 1 My 的离群锆石（用于 BAD 前更关键）。
    此处采用鲁棒的近似：保留落在 median ± max_span/2 内的点。
    """
    ages = np.asarray(ages, dtype=float)
    sigmas = np.asarray(sigmas, dtype=float)

    med = np.median(ages)
    half = max_span_ma / 2.0
    mask = (ages >= med - half) & (ages <= med + half)
    return ages[mask], sigmas[mask]


def bootstrap_min_prior_kde(
    ages: np.ndarray,
    sigmas: np.ndarray,
    n_boot: int = 6000,
    seed: int = 42
) -> gaussian_kde:
    """
    bootstrapped prior 的实用实现：
    - 从 N(age_i, sigma_i) 抽样
    - 每次 bootstrap 取最年轻(min) 作为“喷发年龄候选”
    - 对这些 min 做 KDE 作为 E 的 prior
    """
    rng = np.random.default_rng(seed)
    ages = np.asarray(ages, dtype=float)
    sigmas = np.asarray(sigmas, dtype=float)

    draws = rng.normal(loc=ages[None, :], scale=sigmas[None, :], size=(n_boot, ages.size))
    mins = draws.min(axis=1)
    return gaussian_kde(mins)


def ensure_dir(path: str) -> None:
    import os
    os.makedirs(path, exist_ok=True)
