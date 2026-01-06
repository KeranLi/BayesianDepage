from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class InputData:
    zircon: pd.DataFrame     # rows: zircon grains
    tiepoints: pd.DataFrame  # rows: ash beds with depths


def read_inputs(zircon_csv: str, tiepoints_csv: str) -> InputData:
    z = pd.read_csv(zircon_csv)
    t = pd.read_csv(tiepoints_csv)

    required_z = {"ash_id", "age_ma", "sigma_ma"}
    required_t = {"ash_id", "depth_m"}

    if not required_z.issubset(z.columns):
        raise ValueError(f"zircon.csv 必须包含列：{sorted(required_z)}")
    if not required_t.issubset(t.columns):
        raise ValueError(f"tiepoints.csv 必须包含列：{sorted(required_t)}")

    # 若用户提供了 discordance 标记，默认剔除
    if "is_discordant" in z.columns:
        z = z[z["is_discordant"].fillna(0).astype(int) == 0].copy()

    # 只保留有 depth 的 ash
    z = z.merge(t[["ash_id"]], on="ash_id", how="inner")
    return InputData(zircon=z, tiepoints=t)


def read_query_depths(query_csv: Optional[str], tiepoints: pd.DataFrame, n_grid: int = 300) -> np.ndarray:
    if query_csv:
        qdf = pd.read_csv(query_csv)
        if "depth_m" not in qdf.columns:
            raise ValueError("query_depths.csv 必须包含列：depth_m")
        return qdf["depth_m"].to_numpy(float)

    dmin = float(tiepoints["depth_m"].min())
    dmax = float(tiepoints["depth_m"].max())
    return np.linspace(dmin, dmax, n_grid)
