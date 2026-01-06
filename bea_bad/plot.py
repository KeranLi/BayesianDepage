from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt

from .utils import ensure_dir


def plot_age_depth(
    tie_summary: pd.DataFrame,
    query_summary: pd.DataFrame,
    outdir: str,
    filename: str = "age_depth_model.png",
    invert_y: bool = True
) -> str:
    ensure_dir(outdir)
    fig_path = os.path.join(outdir, filename)

    qq = query_summary["depth_m"].to_numpy(float)
    plt.figure()
    plt.fill_betweenx(
        qq,
        query_summary["age_hdi95_low_ma"].to_numpy(float),
        query_summary["age_hdi95_high_ma"].to_numpy(float),
        alpha=0.3
    )
    plt.plot(query_summary["age_mean_ma"].to_numpy(float), qq)

    plt.errorbar(
        tie_summary["eruption_obs_ma"].to_numpy(float),
        tie_summary["depth_obs_m"].to_numpy(float),
        xerr=1.96 * tie_summary["eruption_obs_sd_ma"].to_numpy(float),
        fmt="o"
    )

    if invert_y:
        plt.gca().invert_yaxis()

    plt.xlabel("Age (Ma)")
    plt.ylabel("Depth (m)")
    plt.title("Bayesian age–depth model (BAD-like) using BEA eruption ages")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()
    return fig_path
