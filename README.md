# BEA → BAD (Python / PyMC)
Reproducible **BEA-like (Bayesian eruption age)** → **BAD-like (Bayesian age–depth)** workflow in Python, following the modeling logic used in Dai et al. (coupled eruption-age inference from single-zircon U–Pb data, then an age–depth model using those eruption ages as tie points).

> This repository provides a practical, open, and editable implementation. It aims to reproduce the *workflow and result behavior* (e.g., age–depth curve with credible intervals), not necessarily a bit-for-bit match to any proprietary/author-specific code.

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

## Dependencies

Recommended (conda):

```bash
conda create -n bea python=3.11
conda activate bea
pip install numpy pandas pymc arviz matplotlib scipy
```

### Speed note (PyTensor / C++ compiler)
If you see warnings like:

- `g++ not detected! PyTensor will be unable to compile C-implementations...`

the code will still run, but sampling can be **much slower**.

**Windows + conda (recommended):**
```bash
conda install -c conda-forge m2w64-toolchain
```

Verify:
```bash
g++ --version
```

**Optional: suppress compilation attempts (does not speed up, only silences warnings)**

PowerShell:
```powershell
$env:PYTENSOR_FLAGS="cxx="
python -m bea_bad --zircon ... --tiepoints ... --outdir out
```

---

## Input data formats

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

## Critical: depth sign convention

The current BAD implementation assumes:

- **Depth increases downward** (larger `depth_m` = deeper)
- **Age increases with depth** (deeper = older)

If your raw depths are negative downward (e.g., -50 m is deeper than -10 m),
convert to downward-positive before modeling:

- `depth_down_m = -depth_m`

The provided example files `zircon_depthdown.csv` and `tiepoints_depthdown.csv`
are already converted to **downward-positive** depths.

---

## Run the workflow

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

## Outputs (in `out/`)

After a successful run you will get:

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

## Common issues

### 1) `No module named bea_bad`
You must run from the directory that contains the `bea_bad/` package folder, and that folder must contain `__init__.py` and `__main__.py`.

Correct command pattern:
```bash
python -m bea_bad --zircon ... --tiepoints ... --outdir out
```

### 2) Age–depth curve goes the “wrong way” (deeper becomes younger)
This is almost always the **depth sign convention**. Ensure your depths are downward-positive (see above).

### 3) Sampling is extremely slow
Install a compiler toolchain (see “Speed note”), then restart your terminal and rerun.

---

## Notes on model choices (high-level)

- **BEA-like:** eruption age `E` is inferred from a set of zircon ages with analytical uncertainty, allowing grains to be older than eruption (a positive offset term). A **bootstrapped prior** (from resampling “youngest plausible ages”) is supported to stabilize inference.
- **BAD-like:** tie-point eruption ages (from BEA) are combined with stratigraphic depths (with optional depth uncertainty) under a monotonic, positive-rate age–depth model to produce an age–depth curve with credible intervals.

---

## Citation / acknowledgement

If you use this workflow in your work, cite the relevant methodological foundations (e.g., BEA and BAD literature) and the study you are reproducing. This code is intended as a transparent, editable reference implementation for research workflows.
