# BayesianDepage (Python / PyMC)

**A reproducible BEA-like (Bayesian eruption age) → BAD-like (Bayesian age–depth) workflow** for single-zircon U–Pb datasets, implemented in Python with **PyMC**.

- **BEA-like:** infer eruption age from a population of zircon ages with analytical uncertainty (allowing older inherited/crystallization ages).
- **BAD-like:** build a monotonic age–depth model using eruption-age tie points (with optional depth uncertainty) and return credible intervals.

> Goal: reproduce the **workflow and result behavior** (e.g., age–depth curve with credible intervals) used in Dai et al., not necessarily a bit-for-bit match to any author-specific/private implementation.

---

## At a glance

- ✅ Works with **CSV** inputs (`zircon.csv`, `tiepoints.csv`)
- ✅ Outputs summary tables + a publication-ready **age–depth plot**
- ✅ Can be packaged as a **Windows GUI .exe** (PyInstaller)

---

## Updates & release notes

**Last updated:** 2026-01-06  
**Current version:** v0.1.0

### Changelog
- **v0.1.0 (2026-01-06)**  
  - Initial BEA→BAD pipeline (PyMC/NUTS)
  - Bootstrapped prior option for BEA
  - Monotonic BAD with optional depth uncertainty (default 0.03 m)
  - CSV outputs + age–depth figure

> Tip: When you publish on GitHub, copy this section into your Release notes and keep the changelog here in sync.

---

## Table of contents

- [Project layout](#project-layout)  
- [Quickstart](#quickstart)  
- [Inputs](#inputs)  
- [Depth sign convention](#depth-sign-convention)  
- [Outputs](#outputs)  
- [Windows GUI app (PyInstaller)](#windows-gui-app-pyinstaller)  
- [Troubleshooting](#troubleshooting)  
- [Model notes](#model-notes)  
- [Citation / acknowledgement](#citation--acknowledgement)

---

## Project layout

```
bea_bad_project/
  bea_bad/
    __init__.py
    __main__.py        # enables: python -m bea_bad ...
    cli.py             # pipeline orchestration
    dataio.py          # input reading & validation
    utils.py           # helpers (MAD, bootstrap prior, filtering)
    bea.py             # BEA-like eruption-age model per ash bed
    bad.py             # BAD-like age–depth model
    plot.py            # plotting/export
  zircon_depthdown.csv
  tiepoints_depthdown.csv
  out/                 # created after running
```

---

## Quickstart

### 1) Install dependencies

Recommended (conda):

```bash
conda create -n bea python=3.11
conda activate bea
pip install numpy pandas pymc arviz matplotlib scipy
```

### 2) Run the pipeline

From the project root (the directory that contains the `bea_bad/` folder):

```bash
python -m bea_bad --zircon zircon_depthdown.csv --tiepoints tiepoints_depthdown.csv --outdir out
```

### Optional: query ages at specific depths

Create `query_depths.csv`:

```csv
depth_m
10
20
30
```

Run:

```bash
python -m bea_bad --zircon zircon_depthdown.csv --tiepoints tiepoints_depthdown.csv --query query_depths.csv --outdir out
```

---

## Inputs

### (1) `zircon.csv` (single-zircon U–Pb ages; one row per grain)

Required columns:
- `ash_id` : ash bed identifier (same for grains from the same bed)
- `age_ma` : age in Ma
- `sigma_ma` : **1σ** uncertainty in Ma

Recommended columns:
- `zircon_id` : grain identifier (useful for traceability)
- `is_discordant` / `omit_flag` : if you already filtered discordant grains

Example:

```csv
ash_id,zircon_id,age_ma,sigma_ma
Gujiao:GJ-ASH-10,GJ10_z4s,251.710,0.0465
...
```

If your uncertainties are given as **2σ**, convert before running:

- `sigma_ma = age_2sigma_ma / 2`

### (2) `tiepoints.csv` (one row per ash bed)

Required columns:
- `ash_id`
- `depth_m` : stratigraphic depth (meters)

Optional:
- `depth_sigma_m` : depth uncertainty (default used by this workflow is **0.03 m ≈ 3 cm**)

Example:

```csv
ash_id,depth_m,depth_sigma_m
Gujiao:GJ-ASH-10,50.8,0.03
...
```

---

## Depth sign convention

The current BAD implementation assumes:

- **Depth increases downward** (larger `depth_m` = deeper)
- **Age increases with depth** (deeper = older)

If your raw depths are negative downward (e.g., -50 m is deeper than -10 m),
convert to downward-positive before modeling:

- `depth_down_m = -depth_m`

The example files `zircon_depthdown.csv` and `tiepoints_depthdown.csv` are already converted to **downward-positive** depths.

---

## Outputs

After a successful run, `out/` will contain:

- `bea_eruption_age_summary.csv`  
  BEA-like eruption-age estimates per ash bed (mean, sd, 95% interval, n grains used)

- `bad_posterior.nc`  
  BAD-like posterior samples (ArviZ NetCDF)

- `tiepoint_summary.csv`  
  Observed eruption ages vs. model-implied tie ages (with 95% intervals)

- `query_age_summary.csv`  
  Age estimates for query depths (or an auto-generated grid)

- `age_depth_model.png`  
  Age–depth curve with 95% credible band + tie points error bars

---

## Windows GUI app (PyInstaller)

If you want a **double-clickable Windows GUI (.exe)**:

1) Create a packaging environment (recommended):

```bat
conda create -n bea_pack python=3.11
conda activate bea_pack
pip install numpy pandas pymc arviz matplotlib scipy
pip install pyinstaller
```

2) Add a GUI entry file `app_gui.py` (Tkinter) that calls the pipeline.

3) Build the executable from the project root:

```bat
python -m PyInstaller --noconfirm --onefile --windowed --name BEA_BAD app_gui.py
```

Output:
- `dist\BEA_BAD.exe`

> Notes:
> - Scientific stacks can produce large executables (hundreds of MB). This is normal.
> - `--onefile` is convenient, but a folder build (no `--onefile`) is sometimes more stable for distribution.

---

## Troubleshooting

### 1) `No module named bea_bad`
Run from the directory that contains the `bea_bad/` folder and ensure it has `__init__.py` and `__main__.py`.

Correct command pattern:

```bash
python -m bea_bad --zircon ... --tiepoints ... --outdir out
```

### 2) Age–depth curve goes the “wrong way” (deeper becomes younger)
This is almost always the **depth sign convention**. Ensure your depths are downward-positive (see above).

### 3) Sampling is extremely slow (PyTensor compiler warnings)
If you see warnings about missing `g++`, the model will still run but can be slower.
On Windows + conda, you can install a toolchain:

```bash
conda install -c conda-forge m2w64-toolchain
```

---

## Model notes

- **BEA-like:** eruption age `E` is inferred from zircon ages with analytical uncertainty, allowing grains to be older than eruption (a positive offset term). A **bootstrapped prior** (from resampling “youngest plausible ages”) is supported to stabilize inference.
- **BAD-like:** tie-point eruption ages (from BEA) are combined with stratigraphic depths (with optional depth uncertainty) under a monotonic, positive-rate age–depth model to produce an age–depth curve with credible intervals.

---

## Citation / acknowledgement

If you use this workflow in your work, cite the relevant methodological foundations (e.g., BEA and BAD literature) and the study you are reproducing. This code is intended as a transparent, editable reference implementation for research workflows.
