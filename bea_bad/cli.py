from __future__ import annotations
import argparse
import os
import pandas as pd

from .dataio import read_inputs, read_query_depths
from .bea import fit_bea_for_ash
from .bad import fit_bad
from .plot import plot_age_depth
from .utils import ensure_dir


def main():
    ap = argparse.ArgumentParser("bea_bad")
    ap.add_argument("--zircon", required=True, help="zircon.csv (ash_id, age_ma, sigma_ma, [is_discordant])")
    ap.add_argument("--tiepoints", required=True, help="tiepoints.csv (ash_id, depth_m)")
    ap.add_argument("--query", default=None, help="query_depths.csv (depth_m). optional")
    ap.add_argument("--outdir", default="out")

    ap.add_argument("--max_span_ma", type=float, default=1.0)
    ap.add_argument("--depth_sigma_m", type=float, default=0.03)
    ap.add_argument("--no_bootstrap_prior", action="store_true")

    ap.add_argument("--bea_draws", type=int, default=2000)
    ap.add_argument("--bea_tune", type=int, default=2000)
    ap.add_argument("--bad_draws", type=int, default=3000)
    ap.add_argument("--bad_tune", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)

    args = ap.parse_args()
    ensure_dir(args.outdir)

    data = read_inputs(args.zircon, args.tiepoints)
    qdepths = read_query_depths(args.query, data.tiepoints)

    # ---- BEA per ash
    rows = []
    for ash_id, g in data.zircon.groupby("ash_id"):
        res = fit_bea_for_ash(
            ash_id=ash_id,
            ages=g["age_ma"].to_numpy(float),
            sigmas=g["sigma_ma"].to_numpy(float),
            use_bootstrap_prior=(not args.no_bootstrap_prior),
            max_span_ma=args.max_span_ma,
            draws=args.bea_draws,
            tune=args.bea_tune,
            seed=args.seed
        )
        rows.append(res.__dict__)

    bea_df = pd.DataFrame(rows).merge(data.tiepoints, on="ash_id", how="left")
    bea_df = bea_df.sort_values("depth_m")
    bea_path = os.path.join(args.outdir, "bea_eruption_age_summary.csv")
    bea_df.to_csv(bea_path, index=False)

    # ---- BAD
    bad_out = fit_bad(
        tie_depths_m=bea_df["depth_m"].to_numpy(float),
        tie_age_mean_ma=bea_df["e_mean"].to_numpy(float),
        tie_age_sd_ma=bea_df["e_sd"].to_numpy(float),
        query_depths_m=qdepths,
        depth_sigma_m=args.depth_sigma_m,
        draws=args.bad_draws,
        tune=args.bad_tune,
        seed=args.seed,
        outdir=args.outdir
    )

    tie_path = os.path.join(args.outdir, "tiepoint_summary.csv")
    query_path = os.path.join(args.outdir, "query_age_summary.csv")
    bad_out.tie_summary.to_csv(tie_path, index=False)
    bad_out.query_summary.to_csv(query_path, index=False)

    fig_path = plot_age_depth(bad_out.tie_summary, bad_out.query_summary, outdir=args.outdir)

    print("Done.")
    print("BEA summary:", bea_path)
    print("BAD posterior:", bad_out.posterior_path)
    print("Tie summary:", tie_path)
    print("Query summary:", query_path)
    print("Figure:", fig_path)
