from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pymc as pm
import arviz as az

from .utils import robust_mad, filter_outliers_within_span, bootstrap_min_prior_kde


@dataclass
class BEAResult:
    ash_id: str
    e_mean: float
    e_sd: float
    hdi95_low: float
    hdi95_high: float
    n_used: int


def fit_bea_for_ash(
    ash_id: str,
    ages: np.ndarray,
    sigmas: np.ndarray,
    *,
    use_bootstrap_prior: bool = True,
    max_span_ma: float = 1.0,
    draws: int = 2000,
    tune: int = 2000,
    chains: int = 2,
    target_accept: float = 0.9,
    seed: int = 42,
) -> BEAResult:
    """
    BEA-like model:
      E = eruption age
      delta_i ~ Exponential(1/tau) (晶体化年龄比喷发更老)
      obs_age_i ~ Normal(E + delta_i, sigma_i)
    E 的 prior：bootstrapped KDE（推荐）或宽正态先验（fallback）
    """
    ages = np.asarray(ages, dtype=float)
    sigmas = np.asarray(sigmas, dtype=float)

    # 可选：按 1 My 规则做鲁棒过滤（论文是 BAD 前做；这里提前做有助于稳定）
    ages2, sigmas2 = filter_outliers_within_span(ages, sigmas, max_span_ma=max_span_ma)
    if ages2.size < 2:
        ages2, sigmas2 = ages, sigmas

    tau_scale = max(robust_mad(ages2), 0.02)

    if use_bootstrap_prior and ages2.size >= 2:
        kde = bootstrap_min_prior_kde(ages2, sigmas2, n_boot=6000, seed=seed)
        grid = np.linspace(ages2.min() - 1.0, ages2.min() + 0.5, 2000)
        pdf = np.clip(kde(grid), 1e-300, None)

        with pm.Model() as m:
            E = pm.Interpolated("E", x_points=grid, pdf_points=pdf)
            tau = pm.HalfNormal("tau", sigma=tau_scale)
            delta = pm.Exponential("delta", lam=1.0 / tau, shape=ages2.size)
            pm.Normal("obs", mu=E + delta, sigma=sigmas2, observed=ages2)

            idata = pm.sample(
                draws=draws, tune=tune, chains=chains,
                target_accept=target_accept, random_seed=seed,
                progressbar=True
            )
    else:
        mu0 = float(ages2.min() - 0.05)
        sd0 = max(float(robust_mad(ages2) * 3), 0.2)

        with pm.Model() as m:
            E = pm.Normal("E", mu=mu0, sigma=sd0)
            tau = pm.HalfNormal("tau", sigma=tau_scale)
            delta = pm.Exponential("delta", lam=1.0 / tau, shape=ages2.size)
            pm.Normal("obs", mu=E + delta, sigma=sigmas2, observed=ages2)

            idata = pm.sample(
                draws=draws, tune=tune, chains=chains,
                target_accept=target_accept, random_seed=seed,
                progressbar=True
            )

    post_E = idata.posterior["E"].values.reshape(-1)
    hdi = az.hdi(post_E, hdi_prob=0.95)

    return BEAResult(
        ash_id=ash_id,
        e_mean=float(np.mean(post_E)),
        e_sd=float(np.std(post_E)),
        hdi95_low=float(hdi[0]),
        hdi95_high=float(hdi[1]),
        n_used=int(ages2.size)
    )
