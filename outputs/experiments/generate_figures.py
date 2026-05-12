"""
Figure Generator — Publication-Quality Plots
CAISc 2026: "AI Scientists Cannot Self-Diagnose Their Own Physics Violations"

Generates three figures from results.json and the synthetic outputs:

  Figure 1 (figure_violation_rates.png):
      Bar chart — Auditor vs Baseline recall by violation type with 95% CI.

  Figure 2 (figure_violation_score_distribution.png):
      Histogram — violation score distribution for clean vs. violating outputs.

  Figure 3 (figure_example_violation.png):
      Two-panel — heatmap of a mass-violation output + mass integral over time.

Run:
    python generate_figures.py

All figures saved to outputs/experiments/figures/ as PNG (300 DPI, tight bbox).
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH  = os.path.join(SCRIPT_DIR, "results.json")
SYNTHETIC_DIR = os.path.join(SCRIPT_DIR, "synthetic_ai_outputs")
FIGURES_DIR   = os.path.join(SCRIPT_DIR, "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

AUDITOR_COLOR  = "#2166AC"   # blue
BASELINE_COLOR = "#D6604D"   # orange-red
CLEAN_COLOR    = "#4DAC26"   # green
VIOL_COLOR     = "#D01C8B"   # magenta

plt.rcParams.update({
    "font.family":     "serif",
    "font.size":       10,
    "axes.labelsize":  11,
    "axes.titlesize":  11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi":      150,
})

# ---------------------------------------------------------------------------
# Wilson CI helper (duplicated to keep module self-contained)
# ---------------------------------------------------------------------------

def wilson_ci(k, n, confidence=0.95):
    if n == 0:
        return (0.0, 0.0, 0.0)
    from scipy import stats as sc_stats
    alpha = 1.0 - confidence
    z = sc_stats.norm.ppf(1 - alpha / 2)
    p_hat = k / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p_hat + z2 / (2 * n)) / denom
    half_width = z * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, centre - half_width), min(1.0, centre + half_width), centre)


# ---------------------------------------------------------------------------
# Figure 1 — Bar chart: recall by violation type
# ---------------------------------------------------------------------------

def figure1_violation_rates(results: dict):
    per_type = results["overall_metrics"]
    pt = results["per_type_metrics"]

    violation_types = ["mass_violation", "bc_drift", "pde_residual",
                       "positivity", "compound"]
    display_names   = ["Mass\nnon-cons.", "BC\ndrift", "PDE\nresidual",
                       "Positivity", "Compound"]

    aud_recalls, aud_lo, aud_hi = [], [], []
    bas_recalls, bas_lo, bas_hi = [], [], []

    for vtype in violation_types:
        if vtype not in pt:
            aud_recalls.append(0); aud_lo.append(0); aud_hi.append(0)
            bas_recalls.append(0); bas_lo.append(0); bas_hi.append(0)
            continue

        entry = pt[vtype]
        n = entry["n"]

        aud_r = entry["auditor_recall"]
        aud_ci = entry["auditor_recall_ci"]   # (lo, hi, centre)
        aud_recalls.append(aud_r)
        aud_lo.append(aud_r - aud_ci[0])
        aud_hi.append(aud_ci[1] - aud_r)

        bas_r = entry["baseline_recall"]
        bas_ci = entry["baseline_recall_ci"]
        bas_recalls.append(bas_r)
        bas_lo.append(bas_r - bas_ci[0])
        bas_hi.append(bas_ci[1] - bas_r)

    x = np.arange(len(violation_types))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6.5, 4.0))

    bars_aud = ax.bar(x - width / 2, [r * 100 for r in aud_recalls], width,
                      label="Physics Auditor",
                      color=AUDITOR_COLOR, alpha=0.88, edgecolor="white", linewidth=0.5)
    ax.errorbar(x - width / 2, [r * 100 for r in aud_recalls],
                yerr=[[e * 100 for e in aud_lo], [e * 100 for e in aud_hi]],
                fmt="none", color="black", capsize=3, linewidth=1.2)

    bars_bas = ax.bar(x + width / 2, [r * 100 for r in bas_recalls], width,
                      label="LLM Baseline (simulated GPT-4)",
                      color=BASELINE_COLOR, alpha=0.88, edgecolor="white", linewidth=0.5)
    ax.errorbar(x + width / 2, [r * 100 for r in bas_recalls],
                yerr=[[e * 100 for e in bas_lo], [e * 100 for e in bas_hi]],
                fmt="none", color="black", capsize=3, linewidth=1.2)

    # Overall recall lines
    aud_overall = results["overall_metrics"]["auditor"]["recall"] * 100
    bas_overall = results["overall_metrics"]["baseline_llm"]["recall"] * 100
    ax.axhline(aud_overall, color=AUDITOR_COLOR,  linestyle="--", linewidth=1.0,
               alpha=0.6, label=f"Auditor overall ({aud_overall:.0f}%)")
    ax.axhline(bas_overall, color=BASELINE_COLOR, linestyle="--", linewidth=1.0,
               alpha=0.6, label=f"Baseline overall ({bas_overall:.0f}%)")

    ax.set_xticks(x)
    ax.set_xticklabels(display_names, ha="center")
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(0, 115)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="lightgray")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "figure_violation_rates.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ---------------------------------------------------------------------------
# Figure 2 — Histogram: violation score distribution
# ---------------------------------------------------------------------------

def figure2_score_distribution(results: dict):
    per_output = results["results"]

    clean_scores = [v["violation_score"] for v in per_output.values()
                    if not v["ground_truth_violated"]]
    viol_scores  = [v["violation_score"] for v in per_output.values()
                    if v["ground_truth_violated"]]

    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    bins = np.linspace(0, 1, 26)
    ax.hist(clean_scores, bins=bins, color=CLEAN_COLOR, alpha=0.75,
            label="Clean outputs (n=8)", edgecolor="white", linewidth=0.4)
    ax.hist(viol_scores,  bins=bins, color=VIOL_COLOR,  alpha=0.70,
            label="Violating outputs (n=32)", edgecolor="white", linewidth=0.4)

    ax.axvline(0.5, color="black", linestyle="--", linewidth=1.0, alpha=0.6,
               label="Decision threshold (0.5)")

    ax.set_xlabel("Violation Score")
    ax.set_ylabel("Count")
    ax.set_xlim(0, 1)
    ax.legend(framealpha=0.9, edgecolor="lightgray")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "figure_violation_score_distribution.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ---------------------------------------------------------------------------
# Figure 3 — Example mass-violation output (heatmap + mass drift)
# ---------------------------------------------------------------------------

def figure3_example_violation():
    # Find the first mass-violation output
    target_id = None
    for fn in sorted(os.listdir(SYNTHETIC_DIR)):
        if not fn.endswith(".json"):
            continue
        fpath = os.path.join(SYNTHETIC_DIR, fn)
        with open(fpath, "r") as f:
            out = json.load(f)
        if out.get("injected_violation") == "mass_violation":
            target_id = out
            break

    if target_id is None:
        print("  WARNING: No mass-violation output found — skipping Figure 3")
        return

    out = target_id
    Nx = int(out["Nx"])
    Nt = int(out["Nt"])
    x  = np.array(out["grid_x"])
    t  = np.array(out["grid_t"])
    u  = np.array(out["solution"]) if isinstance(out["solution"][0], list) \
         else np.array(out["solution"]).reshape(Nt, Nx)

    mass = np.trapz(u, x, axis=1)
    mass_pct_change = (mass - mass[0]) / abs(mass[0] + 1e-12) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 3.5))

    # Left panel: solution heatmap u(x, t)
    cmap = LinearSegmentedColormap.from_list(
        "physics", ["#FFFFFF", "#74C0E8", "#2166AC", "#0D0D66"]
    )
    im = ax1.imshow(u, aspect="auto", origin="lower",
                    extent=[x[0], x[-1], t[0], t[-1]],
                    cmap=cmap, vmin=u.min(), vmax=u.max())
    plt.colorbar(im, ax=ax1, label="u(x, t)", shrink=0.85)
    ax1.set_xlabel("x")
    ax1.set_ylabel("t")
    ax1.set_title(f"Solution field — {out['id']}")

    # Right panel: total mass over time
    ax2.plot(t, mass, color=VIOL_COLOR, linewidth=1.8, label="Total mass $M(t)$")
    ax2.axhline(mass[0], color="black", linestyle="--", linewidth=1.0,
                alpha=0.5, label=f"$M(0) = {mass[0]:.4f}$")
    ax2.fill_between(t, mass[0], mass, alpha=0.15, color=VIOL_COLOR)

    max_drift = float(np.max(np.abs(mass_pct_change)))
    ax2.set_xlabel("Time t")
    ax2.set_ylabel("$\\int u\\,dx$")
    ax2.set_title(f"Mass drift: {max_drift:.1f}% (injected {out['injected_severity']*100:.1f}%)")
    ax2.legend(framealpha=0.9, edgecolor="lightgray")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(linestyle=":", alpha=0.4)

    fig.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "figure_example_violation.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not os.path.isfile(RESULTS_PATH):
        print(f"ERROR: {RESULTS_PATH} not found. Run run_experiment.py first.")
        return

    with open(RESULTS_PATH, "r") as f:
        results = json.load(f)

    print("Generating figures...")
    figure1_violation_rates(results)
    figure2_score_distribution(results)
    figure3_example_violation()
    print(f"\nAll figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
