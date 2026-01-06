from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
import pymc as pm


@dataclass
class BADOutputs:
    tie_summary: pd.DataFrame
    query_summary: pd.DataFrame
    posterior_path: str


def _piecewise_age_one_draw(d_tie: np.ndarray, age0: float, rates: np.ndarray, d_query: np.ndarray) -> np.ndarray:
    seg_len = np.diff(d_tie)
    age_tie = np.empty_like(d_tie, dtype=float)
    age_tie[0] = age0
    age_tie[1:] = age0 + np.cumsum(rates * seg_len)

    idx = np.searchsorted(d_tie, d_query, side="right") - 1
    idx = np.clip(idx, 0, len(d_tie) - 2)

    return age_tie[idx] + rates[idx] * (d_query - d_tie[idx])


def fit_bad(
    tie_depths_m: np.ndarray,
    tie_age_mean_ma: np.ndarray,
    tie_age_sd_ma: np.ndarray,
    query_depths_m: np.ndarray,
    *,
    depth_sigma_m: float = 0.03,            # 约等于 ±3 cm 的层位不确定度实现
    sedrate_logn_mu: float = np.log(0.05),  # Ma/m（你可按剖面规模改）
    sedrate_logn_sigma: float = 1.0,
    draws: int = 3000,
    tune: int = 3000,
    chains: int = 2,
    target_accept: float = 0.9,
    seed: int = 42,
    outdir: str = "out",
) -> BADOutputs:
    import os
    from .utils import ensure_dir

    ensure_dir(outdir)

    d_obs = np.asarray(tie_depths_m, dtype=float)
    E_obs = np.asarray(tie_age_mean_ma, dtype=float)
    E_sd = np.asarray(tie_age_sd_ma, dtype=float)
    q = np.asarray(query_depths_m, dtype=float)

    # 排序很关键（ordered transform 需要单调深度）
    order = np.argsort(d_obs)
    d_obs = d_obs[order]
    E_obs = E_obs[order]
    E_sd = E_sd[order]

    K = d_obs.size
    if K < 2:
        raise ValueError("BAD 至少需要 2 个 tie points")

    with pm.Model() as m:
        d_true = pm.Normal(
            "d_true",
            mu=d_obs,
            sigma=depth_sigma_m,
            shape=K,
            transform=pm.distributions.transforms.ordered,
            initval=d_obs
        )

        rates = pm.LogNormal("rates", mu=sedrate_logn_mu, sigma=sedrate_logn_sigma, shape=K - 1)

        age0 = pm.Normal("age0", mu=E_obs[0], sigma=max(float(E_sd[0] * 5), 0.2))

        seg_len = d_true[1:] - d_true[:-1]
        age_ties = pm.Deterministic("age_ties", pm.math.concatenate([[age0], age0 + pm.math.cumsum(rates * seg_len)]))

        pm.Normal("E_like", mu=age_ties, sigma=E_sd, observed=E_obs)

        idata = pm.sample(
            draws=draws, tune=tune, chains=chains,
            target_accept=target_accept, random_seed=seed,
            progressbar=True
        )

    posterior_path = os.path.join(outdir, "bad_posterior.nc")
    idata.to_netcdf(posterior_path)

    # posterior arrays
    d_true_draws = idata.posterior["d_true"].values.reshape(-1, K)
    age0_draws = idata.posterior["age0"].values.reshape(-1)
    rates_draws = idata.posterior["rates"].values.reshape(-1, K - 1)

    # query ages
    ages_q = np.empty((d_true_draws.shape[0], q.size), dtype=float)
    for i in range(d_true_draws.shape[0]):
        ages_q[i] = _piecewise_age_one_draw(d_true_draws[i], age0_draws[i], rates_draws[i], q)

    query_summary = pd.DataFrame({
        "depth_m": q,
        "age_mean_ma": ages_q.mean(axis=0),
        "age_hdi95_low_ma": np.quantile(ages_q, 0.025, axis=0),
        "age_hdi95_high_ma": np.quantile(ages_q, 0.975, axis=0),
    }).sort_values("depth_m")

    # tie ages summary
    tie_ages = np.empty((d_true_draws.shape[0], K), dtype=float)
    for i in range(d_true_draws.shape[0]):
        seg_len = np.diff(d_true_draws[i])
        tie_ages[i, 0] = age0_draws[i]
        tie_ages[i, 1:] = age0_draws[i] + np.cumsum(rates_draws[i] * seg_len)

    tie_summary = pd.DataFrame({
        "depth_obs_m": d_obs,
        "eruption_obs_ma": E_obs,
        "eruption_obs_sd_ma": E_sd,
        "age_model_mean_ma": tie_ages.mean(axis=0),
        "age_model_hdi95_low_ma": np.quantile(tie_ages, 0.025, axis=0),
        "age_model_hdi95_high_ma": np.quantile(tie_ages, 0.975, axis=0),
    })

    return BADOutputs(
        tie_summary=tie_summary,
        query_summary=query_summary,
        posterior_path=posterior_path
    )
