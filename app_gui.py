# app_gui.py  (Windows GUI launcher for BEA→BAD, with tunable sampling settings)
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


def browse_csv(var):
    p = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if p:
        var.set(p)


def browse_outdir(var):
    p = filedialog.askdirectory(title="Select output folder")
    if p:
        var.set(p)


def _parse_int(name: str, value: str, min_v: int = 1) -> int:
    try:
        v = int(value)
    except Exception:
        raise ValueError(f"{name} must be an integer.")
    if v < min_v:
        raise ValueError(f"{name} must be ≥ {min_v}.")
    return v


def _parse_float(name: str, value: str, min_v=None, max_v=None) -> float:
    try:
        v = float(value)
    except Exception:
        raise ValueError(f"{name} must be a number.")
    if min_v is not None and v < min_v:
        raise ValueError(f"{name} must be ≥ {min_v}.")
    if max_v is not None and v > max_v:
        raise ValueError(f"{name} must be ≤ {max_v}.")
    return v


def run_pipeline():
    zircon = zircon_var.get().strip()
    tiepoints = tiepoints_var.get().strip()
    outdir = outdir_var.get().strip() or "out"

    if not zircon or not Path(zircon).exists():
        messagebox.showerror("Missing input", "Please select a valid zircon CSV file.")
        return
    if not tiepoints or not Path(tiepoints).exists():
        messagebox.showerror("Missing input", "Please select a valid tiepoints CSV file.")
        return

    try:
        # Read & validate UI parameters
        bea_draws = _parse_int("BEA draws", bea_draws_var.get(), 100)
        bea_tune = _parse_int("BEA tune", bea_tune_var.get(), 100)
        bad_draws = _parse_int("BAD draws", bad_draws_var.get(), 100)
        bad_tune = _parse_int("BAD tune", bad_tune_var.get(), 100)

        max_span_ma = _parse_float("Max span (Ma)", max_span_var.get(), 0.0, 100.0)
        depth_sigma_m = _parse_float("Depth sigma (m)", depth_sigma_var.get(), 0.0, 10.0)
        target_accept = _parse_float("target_accept", target_accept_var.get(), 0.6, 0.999)

        no_bootstrap = bool(no_bootstrap_var.get())

        # Call the internal CLI entry point
        from bea_bad.cli import main

        # Build argv
        argv = [
            "bea_bad",
            "--zircon", zircon,
            "--tiepoints", tiepoints,
            "--outdir", outdir,

            "--bea_draws", str(bea_draws),
            "--bea_tune", str(bea_tune),
            "--bad_draws", str(bad_draws),
            "--bad_tune", str(bad_tune),

            "--max_span_ma", str(max_span_ma),
            "--depth_sigma_m", str(depth_sigma_m),
        ]

        # If your cli.py doesn't have --target_accept yet, either add it there,
        # or remove these two lines.
        argv += ["--target_accept", str(target_accept)]

        if no_bootstrap:
            argv.append("--no_bootstrap_prior")

        sys.argv = argv
        main()

        messagebox.showinfo("Done", f"Finished!\nOutputs saved to:\n{Path(outdir).resolve()}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# --- GUI layout ---
root = tk.Tk()
root.title("BEA → BAD (Bayesian eruption age + age–depth)")
root.geometry("860x420")

zircon_var = tk.StringVar()
tiepoints_var = tk.StringVar()
outdir_var = tk.StringVar(value="out")

# Defaults (sane for a first run)
bea_draws_var = tk.StringVar(value="2000")
bea_tune_var = tk.StringVar(value="2000")
bad_draws_var = tk.StringVar(value="3000")
bad_tune_var = tk.StringVar(value="3000")

max_span_var = tk.StringVar(value="1.0")
depth_sigma_var = tk.StringVar(value="0.03")
target_accept_var = tk.StringVar(value="0.9")

no_bootstrap_var = tk.IntVar(value=0)

padx = 10
pady = 8

# ---- Inputs frame
inputs = tk.LabelFrame(root, text="Inputs", padx=10, pady=10)
inputs.pack(fill="x", padx=10, pady=10)

tk.Label(inputs, text="Zircon CSV").grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
tk.Entry(inputs, textvariable=zircon_var, width=78).grid(row=0, column=1, padx=padx, pady=pady)
tk.Button(inputs, text="Browse", command=lambda: browse_csv(zircon_var)).grid(row=0, column=2, padx=padx, pady=pady)

tk.Label(inputs, text="Tiepoints CSV").grid(row=1, column=0, sticky="w", padx=padx, pady=pady)
tk.Entry(inputs, textvariable=tiepoints_var, width=78).grid(row=1, column=1, padx=padx, pady=pady)
tk.Button(inputs, text="Browse", command=lambda: browse_csv(tiepoints_var)).grid(row=1, column=2, padx=padx, pady=pady)

tk.Label(inputs, text="Output folder").grid(row=2, column=0, sticky="w", padx=padx, pady=pady)
tk.Entry(inputs, textvariable=outdir_var, width=78).grid(row=2, column=1, padx=padx, pady=pady)
tk.Button(inputs, text="Browse", command=lambda: browse_outdir(outdir_var)).grid(row=2, column=2, padx=padx, pady=pady)

# ---- Parameters frame
params = tk.LabelFrame(root, text="Model / Sampling parameters", padx=10, pady=10)
params.pack(fill="x", padx=10, pady=10)

# Row 0
tk.Label(params, text="BEA draws").grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=bea_draws_var, width=12).grid(row=0, column=1, sticky="w", padx=padx, pady=pady)

tk.Label(params, text="BEA tune").grid(row=0, column=2, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=bea_tune_var, width=12).grid(row=0, column=3, sticky="w", padx=padx, pady=pady)

tk.Label(params, text="BAD draws").grid(row=0, column=4, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=bad_draws_var, width=12).grid(row=0, column=5, sticky="w", padx=padx, pady=pady)

tk.Label(params, text="BAD tune").grid(row=0, column=6, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=bad_tune_var, width=12).grid(row=0, column=7, sticky="w", padx=padx, pady=pady)

# Row 1
tk.Label(params, text="Max span (Ma)").grid(row=1, column=0, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=max_span_var, width=12).grid(row=1, column=1, sticky="w", padx=padx, pady=pady)

tk.Label(params, text="Depth sigma (m)").grid(row=1, column=2, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=depth_sigma_var, width=12).grid(row=1, column=3, sticky="w", padx=padx, pady=pady)

tk.Label(params, text="target_accept").grid(row=1, column=4, sticky="w", padx=padx, pady=pady)
tk.Entry(params, textvariable=target_accept_var, width=12).grid(row=1, column=5, sticky="w", padx=padx, pady=pady)

tk.Checkbutton(params, text="Disable bootstrap prior (BEA)", variable=no_bootstrap_var)\
    .grid(row=1, column=6, columnspan=2, sticky="w", padx=padx, pady=pady)

# ---- Run button
tk.Button(root, text="Run", command=run_pipeline, height=2, width=14).pack(pady=18)

root.mainloop()
