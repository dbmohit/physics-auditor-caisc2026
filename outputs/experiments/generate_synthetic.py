"""
Synthetic AI Output Generator
CAISc 2026: "AI Scientists Cannot Self-Diagnose Their Own Physics Violations"

Generates N=40 synthetic PINN outputs for the 1D diffusion equation:
    du/dt = D * d²u/dx²
    Domain: x in [0, 1], t in [0, 1]
    IC:     u(x, 0) = sin(pi * x)
    BC:     u(0, t) = u(1, t) = 0
    Exact:  u(x, t) = sin(pi * x) * exp(-D * pi^2 * t)

Distribution (exactly 40 outputs):
    indices 000-007 : clean (no violations)          — 8 outputs
    indices 008-015 : mass conservation violations   — 8 outputs
    indices 016-023 : BC drift violations            — 8 outputs
    indices 024-031 : PDE residual violations        — 8 outputs
    indices 032-035 : positivity violations          — 4 outputs
    indices 036-039 : compound violations (2+ types) — 4 outputs

Run:
    python generate_synthetic.py
"""

import os
import json
import math
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "synthetic_ai_outputs")
LABELS_PATH = os.path.join(SCRIPT_DIR, "violation_labels.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Problem parameters
# ---------------------------------------------------------------------------

D_TRUE = 0.1        # true diffusivity
NX = 64             # spatial grid points
NT = 100            # time grid points
RNG_SEED = 42       # reproducibility

rng = np.random.default_rng(RNG_SEED)

# ---------------------------------------------------------------------------
# Analytical solution helpers
# ---------------------------------------------------------------------------

def make_grids(Nx=NX, Nt=NT):
    x = np.linspace(0.0, 1.0, Nx)
    t = np.linspace(0.0, 1.0, Nt)
    return x, t


def exact_solution(x, t, D=D_TRUE):
    """u(x, t) = sin(pi*x) * exp(-D * pi^2 * t)"""
    X, T = np.meshgrid(x, t)            # (Nt, Nx)
    return np.sin(math.pi * X) * np.exp(-D * math.pi ** 2 * T)


def pde_residual_1d_diffusion(u, x, t, D=D_TRUE):
    """
    Compute PDE residual r = du/dt - D * d²u/dx²
    at N_test=200 random interior points using finite differences.
    Returns array of shape (N_test,).
    """
    Nt, Nx = u.shape
    dx = x[1] - x[0]
    dt = t[1] - t[0]

    rng_local = np.random.default_rng(99)
    ti_vals = rng_local.integers(1, Nt - 1, size=200)
    xi_vals = rng_local.integers(1, Nx - 1, size=200)

    residuals = []
    for ti, xi in zip(ti_vals, xi_vals):
        dudt   = (u[ti + 1, xi] - u[ti - 1, xi]) / (2 * dt)
        d2udx2 = (u[ti, xi + 1] - 2 * u[ti, xi] + u[ti, xi - 1]) / (dx ** 2)
        r = dudt - D * d2udx2
        residuals.append(r)
    return np.array(residuals)


def small_noise(shape, scale=1e-4, rng=rng):
    """Small Gaussian noise to simulate PINN numerical noise."""
    return rng.normal(0, scale, shape)


# ---------------------------------------------------------------------------
# Violation injectors
# ---------------------------------------------------------------------------

def inject_mass_violation(u, t, severity=None):
    """
    Multiply solution by a slowly growing factor (1 + alpha * t/T_max).
    alpha drawn from [0.08, 0.15] to guarantee > 5% mass drift.
    """
    alpha = rng.uniform(0.08, 0.15) if severity is None else severity
    T_max = t[-1]
    factor = 1.0 + alpha * (t / T_max)   # shape (Nt,)
    u_viol = u * factor[:, np.newaxis]
    return u_viol, float(alpha)


def inject_bc_drift(u, t, severity=None):
    """
    Add a sinusoidal BC perturbation that grows with t.
    Adds amplitude * sin(2*pi*t/T) * bump(x) to the solution.
    amplitude in [0.15, 0.30].
    """
    Nt, Nx = u.shape
    amplitude = rng.uniform(0.15, 0.30) if severity is None else severity
    x = np.linspace(0.0, 1.0, Nx)
    T_max = t[-1]

    # Boundary bump: concentrated near x=0 and x=1
    # left boundary perturbation
    left_bump  = np.exp(-50 * x ** 2)           # peaks at x=0
    right_bump = np.exp(-50 * (x - 1.0) ** 2)  # peaks at x=1

    perturbation = np.zeros_like(u)
    for ti, tv in enumerate(t):
        growth = (tv / T_max) ** 1.5
        perturbation[ti] = amplitude * growth * (
            np.sin(2 * math.pi * tv) * left_bump +
            np.cos(2 * math.pi * tv) * right_bump
        )
    return u + perturbation, float(amplitude)


def inject_pde_violation(x, t, severity=None):
    """
    Use wrong diffusivity D' = D_TRUE + delta_D.
    delta_D in [0.15, 0.35], giving wrong decay rate.
    The PDE residual when evaluated at true D will be large.
    """
    delta_D = rng.uniform(0.15, 0.35) if severity is None else severity
    D_wrong = D_TRUE + delta_D
    u_wrong = exact_solution(x, t, D=D_wrong)
    return u_wrong, float(delta_D)


def inject_positivity_violation(u, severity=None):
    """
    Subtract an offset to push min below zero.
    offset in [0.05, 0.15].
    """
    offset = rng.uniform(0.05, 0.15) if severity is None else severity
    u_viol = u - offset
    return u_viol, float(offset)


def compute_pde_test_residuals(u, x, t, D=D_TRUE):
    """Wrapper returning 200 PDE residuals at interior test points."""
    return pde_residual_1d_diffusion(u, x, t, D=D)


# ---------------------------------------------------------------------------
# Build a single output dict
# ---------------------------------------------------------------------------

def build_output(
    idx: int,
    violation_type: str,
    u: np.ndarray,
    x: np.ndarray,
    t: np.ndarray,
    injected_severity: float,
    D_used: float = D_TRUE,
) -> dict:
    """Package a PINN output into the canonical JSON schema."""

    # PDE residuals evaluated at true D (exposes wrong-D outputs)
    pde_residuals = compute_pde_test_residuals(u, x, t, D=D_TRUE)

    output = {
        "id": f"output_{idx:03d}",
        "problem": "1d_diffusion",
        "D": D_TRUE,
        "grid_x": x.tolist(),
        "grid_t": t.tolist(),
        "solution": u.tolist(),         # (Nt, Nx) nested list
        "Nx": int(NX),
        "Nt": int(NT),
        "injected_violation": violation_type,
        "injected_severity": injected_severity,
        "pde_test_residuals": pde_residuals.tolist(),
    }
    return output


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def generate_all():
    x, t = make_grids()
    u_clean_base = exact_solution(x, t, D=D_TRUE)

    labels = {}
    generated = []

    idx = 0

    # ------------------------------------------------------------------ #
    # 000-007 : CLEAN  (8 outputs)
    # ------------------------------------------------------------------ #
    for i in range(8):
        noise_scale = rng.uniform(5e-5, 2e-4)
        u = u_clean_base + small_noise(u_clean_base.shape, scale=noise_scale)
        severity = float(noise_scale)
        out = build_output(idx, "none", u, x, t, injected_severity=0.0)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": False, "violation_type": "none"}
        idx += 1

    # ------------------------------------------------------------------ #
    # 008-015 : MASS VIOLATION  (8 outputs)
    # ------------------------------------------------------------------ #
    for i in range(8):
        u_base = u_clean_base + small_noise(u_clean_base.shape, scale=1e-4)
        u_viol, sev = inject_mass_violation(u_base, t)
        out = build_output(idx, "mass_violation", u_viol, x, t, injected_severity=sev)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": True, "violation_type": "mass_violation"}
        idx += 1

    # ------------------------------------------------------------------ #
    # 016-023 : BC DRIFT  (8 outputs)
    # ------------------------------------------------------------------ #
    for i in range(8):
        u_base = u_clean_base + small_noise(u_clean_base.shape, scale=1e-4)
        u_viol, sev = inject_bc_drift(u_base, t)
        out = build_output(idx, "bc_drift", u_viol, x, t, injected_severity=sev)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": True, "violation_type": "bc_drift"}
        idx += 1

    # ------------------------------------------------------------------ #
    # 024-031 : PDE RESIDUAL VIOLATION  (8 outputs)
    # ------------------------------------------------------------------ #
    for i in range(8):
        u_wrong, sev = inject_pde_violation(x, t)
        u_wrong += small_noise(u_wrong.shape, scale=1e-4)
        out = build_output(idx, "pde_residual", u_wrong, x, t, injected_severity=sev)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": True, "violation_type": "pde_residual"}
        idx += 1

    # ------------------------------------------------------------------ #
    # 032-035 : POSITIVITY VIOLATION  (4 outputs)
    # ------------------------------------------------------------------ #
    for i in range(4):
        u_base = u_clean_base + small_noise(u_clean_base.shape, scale=1e-4)
        u_viol, sev = inject_positivity_violation(u_base)
        out = build_output(idx, "positivity", u_viol, x, t, injected_severity=sev)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": True, "violation_type": "positivity"}
        idx += 1

    # ------------------------------------------------------------------ #
    # 036-039 : COMPOUND  (4 outputs — mass + BC drift simultaneously)
    # ------------------------------------------------------------------ #
    for i in range(4):
        u_base = u_clean_base + small_noise(u_clean_base.shape, scale=1e-4)
        u_mass, sev_mass = inject_mass_violation(u_base, t)
        u_comp, sev_bc   = inject_bc_drift(u_mass, t)
        sev_compound = float(sev_mass + sev_bc)
        out = build_output(idx, "compound", u_comp, x, t, injected_severity=sev_compound)
        generated.append(out)
        labels[f"output_{idx:03d}"] = {"has_violation": True, "violation_type": "compound"}
        idx += 1

    # ------------------------------------------------------------------ #
    # Save all outputs
    # ------------------------------------------------------------------ #
    assert idx == 40, f"Expected 40 outputs, got {idx}"

    for out in generated:
        path = os.path.join(OUTPUT_DIR, f"{out['id']}.json")
        with open(path, "w") as f:
            json.dump(out, f)
        print(f"  Saved {out['id']} ({out['injected_violation']})")

    with open(LABELS_PATH, "w") as f:
        json.dump(labels, f, indent=2)

    print(f"\nGenerated {len(generated)} outputs → {OUTPUT_DIR}")
    print(f"Labels saved → {LABELS_PATH}")

    # Summary
    type_counts = {}
    for v in labels.values():
        vt = v["violation_type"]
        type_counts[vt] = type_counts.get(vt, 0) + 1
    print("\nDistribution:")
    for vt, count in sorted(type_counts.items()):
        print(f"  {vt:20s}: {count}")


if __name__ == "__main__":
    generate_all()
