"""
Physics Auditor — Core Module
CAISc 2026: "AI Scientists Cannot Self-Diagnose Their Own Physics Violations"

Runs conservation law checks on PINN solution outputs.
Usage:
    from physics_auditor import PhysicsAuditor
    auditor = PhysicsAuditor()
    report = auditor.audit(output_dict)

Verify mode:
    python physics_auditor.py --verify results.json
"""

import sys
import json
import math
import argparse
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable


# ---------------------------------------------------------------------------
# ViolationReport dataclass
# ---------------------------------------------------------------------------

@dataclass
class ViolationReport:
    violation_type: str          # "mass", "bc", "pde", "positivity", "compound", "none"
    detected: bool
    severity: float              # 0.0 (clean) to 1.0 (maximally violating)
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# PhysicsAuditor class
# ---------------------------------------------------------------------------

class PhysicsAuditor:
    """
    Lightweight physics consistency checker for PINN solution outputs.

    All epsilon values are acceptance thresholds — a metric exceeding its
    epsilon triggers a violation flag.

    Parameters
    ----------
    epsilon_mass : float
        Relative mass conservation tolerance. Default 0.05 (5%).
    epsilon_energy : float
        Relative energy conservation tolerance. Default 0.05.
    epsilon_bc : float
        Maximum allowed absolute boundary residual. Default 0.1.
    epsilon_pde : float
        Maximum allowed mean-squared PDE residual. Default 0.05.
    epsilon_positivity : float
        Minimum allowed solution value (concentration). Default -0.01.
    epsilon_symmetry : float
        Maximum allowed symmetry error. Default 0.01.
    """

    def __init__(
        self,
        epsilon_mass: float = 0.05,
        epsilon_energy: float = 0.05,
        epsilon_bc: float = 0.1,
        epsilon_pde: float = 0.05,
        epsilon_positivity: float = -0.01,
        epsilon_symmetry: float = 0.01,
    ):
        self.epsilon_mass = epsilon_mass
        self.epsilon_energy = epsilon_energy
        self.epsilon_bc = epsilon_bc
        self.epsilon_pde = epsilon_pde
        self.epsilon_positivity = epsilon_positivity
        self.epsilon_symmetry = epsilon_symmetry

    # ------------------------------------------------------------------
    # Individual check methods
    # ------------------------------------------------------------------

    def check_mass_conservation(
        self, C: np.ndarray, x: np.ndarray, t: np.ndarray
    ) -> dict:
        """
        Check mass (spatial integral) conservation over time.

        Parameters
        ----------
        C : ndarray, shape (Nt, Nx)
            Concentration/solution field.
        x : ndarray, shape (Nx,)
            Spatial grid coordinates.
        t : ndarray, shape (Nt,)
            Time grid coordinates.

        Returns
        -------
        dict with keys: violation, max_relative_error, epsilon, score,
                        mass_at_each_t
        """
        # Integrate over x using trapezoidal rule at each timestep
        mass = np.trapz(C, x, axis=1)          # shape (Nt,)
        mass_0 = mass[0]

        if abs(mass_0) < 1e-12:
            # Trivially zero — no meaningful conservation check
            return {
                "violation": False,
                "max_relative_error": 0.0,
                "epsilon": self.epsilon_mass,
                "score": 0.0,
                "mass_at_each_t": mass.tolist(),
                "note": "initial mass near zero — check skipped",
            }

        relative_errors = np.abs(mass - mass_0) / abs(mass_0)
        max_relative_error = float(np.max(relative_errors))
        violation = max_relative_error > self.epsilon_mass

        # score: how far above threshold, clipped to [0, 1]
        score = float(np.clip(max_relative_error / (self.epsilon_mass + 1e-9), 0.0, 1.0))
        score = min(score, 1.0)

        return {
            "violation": bool(violation),
            "max_relative_error": max_relative_error,
            "epsilon": self.epsilon_mass,
            "score": score,
            "mass_at_each_t": mass.tolist(),
        }

    def check_energy_conservation(
        self, u: np.ndarray, x: np.ndarray, t: np.ndarray
    ) -> dict:
        """
        Check L2 energy conservation: ||u||_2 should not grow anomalously.

        Parameters
        ----------
        u : ndarray, shape (Nt, Nx)
        x : ndarray, shape (Nx,)
        t : ndarray, shape (Nt,)
        """
        energy = np.trapz(u ** 2, x, axis=1)   # shape (Nt,)
        energy_0 = energy[0]

        if abs(energy_0) < 1e-12:
            return {
                "violation": False,
                "max_relative_error": 0.0,
                "epsilon": self.epsilon_energy,
                "score": 0.0,
                "note": "initial energy near zero — check skipped",
            }

        relative_errors = np.abs(energy - energy_0) / abs(energy_0)
        max_relative_error = float(np.max(relative_errors))
        violation = max_relative_error > self.epsilon_energy
        score = float(np.clip(max_relative_error / (self.epsilon_energy + 1e-9), 0.0, 1.0))

        return {
            "violation": bool(violation),
            "max_relative_error": max_relative_error,
            "epsilon": self.epsilon_energy,
            "score": score,
        }

    def check_bc_drift(
        self,
        u_boundary_left: np.ndarray,
        u_boundary_right: np.ndarray,
        expected_left: float = 0.0,
        expected_right: float = 0.0,
    ) -> dict:
        """
        Check boundary condition drift over time.

        Parameters
        ----------
        u_boundary_left  : ndarray, shape (Nt,) — solution at x=0 over time
        u_boundary_right : ndarray, shape (Nt,) — solution at x=1 over time
        expected_left    : expected BC value at left boundary
        expected_right   : expected BC value at right boundary
        """
        residuals_left  = np.abs(u_boundary_left  - expected_left)
        residuals_right = np.abs(u_boundary_right - expected_right)
        max_residual = float(max(np.max(residuals_left), np.max(residuals_right)))
        violation = max_residual > self.epsilon_bc
        score = float(np.clip(max_residual / (self.epsilon_bc + 1e-9), 0.0, 1.0))

        return {
            "violation": bool(violation),
            "max_residual": max_residual,
            "max_residual_left": float(np.max(residuals_left)),
            "max_residual_right": float(np.max(residuals_right)),
            "epsilon": self.epsilon_bc,
            "score": score,
        }

    def check_pde_residual(
        self,
        pde_test_residuals: np.ndarray,
    ) -> dict:
        """
        Check mean-squared PDE residual at held-out test points.

        Parameters
        ----------
        pde_test_residuals : ndarray, shape (N_test,)
            PDE residual values at test points NOT used in training.
        """
        msr = float(np.mean(pde_test_residuals ** 2))
        violation = msr > self.epsilon_pde
        score = float(np.clip(msr / (self.epsilon_pde + 1e-9), 0.0, 1.0))

        return {
            "violation": bool(violation),
            "mean_squared_residual": msr,
            "mean_abs_residual": float(np.mean(np.abs(pde_test_residuals))),
            "epsilon": self.epsilon_pde,
            "score": score,
        }

    def check_positivity(self, u: np.ndarray) -> dict:
        """
        Check positivity constraint: solution must stay >= epsilon_positivity.

        Parameters
        ----------
        u : ndarray, any shape
        """
        min_value = float(np.min(u))
        violation = min_value < self.epsilon_positivity
        negative_fraction = float(np.mean(u < 0.0))

        # score: magnitude of violation relative to a reference scale of 0.1
        score = float(np.clip(abs(min(min_value, 0.0)) / 0.1, 0.0, 1.0)) if violation else 0.0

        return {
            "violation": bool(violation),
            "min_value": min_value,
            "negative_fraction": negative_fraction,
            "epsilon": self.epsilon_positivity,
            "score": score,
        }

    def check_symmetry(
        self, u: np.ndarray, symmetry_axis: str = "x"
    ) -> dict:
        """
        Check left-right (x-axis) or top-bottom symmetry of solution field.

        Parameters
        ----------
        u : ndarray, shape (Nt, Nx) or (Nt, Nx, Ny)
        symmetry_axis : "x" or "y"
        """
        if symmetry_axis == "x":
            u_flipped = u[..., ::-1]
        else:
            # y-axis: flip along second spatial dimension
            if u.ndim < 3:
                return {
                    "violation": False,
                    "symmetry_error": 0.0,
                    "epsilon": self.epsilon_symmetry,
                    "score": 0.0,
                    "note": "y-symmetry requires 3D array",
                }
            u_flipped = u[:, ::-1, :]

        symmetry_error = float(np.mean(np.abs(u - u_flipped)))
        violation = symmetry_error > self.epsilon_symmetry
        score = float(np.clip(symmetry_error / (self.epsilon_symmetry + 1e-9), 0.0, 1.0))

        return {
            "violation": bool(violation),
            "symmetry_error": symmetry_error,
            "epsilon": self.epsilon_symmetry,
            "score": score,
        }

    # ------------------------------------------------------------------
    # Main audit method — operates on the standard JSON dict schema
    # ------------------------------------------------------------------

    def audit(self, output: dict) -> dict:
        """
        Run all applicable checks on a PINN output dict.

        The dict must conform to the schema in dispatch.md (generated by
        generate_synthetic_outputs.py).

        Returns
        -------
        dict with keys:
            id, overall_pass, violation_score, checks (per-check results),
            n_violations_detected, predicted_violation_type
        """
        output_id = output.get("id", "unknown")
        Nx = int(output["Nx"])
        Nt = int(output["Nt"])

        grid_x = np.array(output["grid_x"], dtype=float)
        grid_t = np.array(output["grid_t"], dtype=float)

        # solution is stored flattened row-major (Nt * Nx,) or as nested list
        sol_raw = output["solution"]
        if isinstance(sol_raw[0], list):
            C = np.array(sol_raw, dtype=float)          # (Nt, Nx)
        else:
            C = np.array(sol_raw, dtype=float).reshape(Nt, Nx)

        checks = {}

        # 1. Mass conservation — for Dirichlet diffusion, compare against
        # expected exponential decay m0 * exp(-D * pi^2 * t) instead of
        # constant mass (which is only valid for conservative systems).
        D = float(output.get("D", 0.1))
        if output.get("problem") == "1d_diffusion" and abs(D) > 1e-9:
            m0_exact = 2.0 / math.pi          # ∫₀¹ sin(πx)dx
            expected_mass = m0_exact * np.exp(-D * math.pi ** 2 * grid_t)
            actual_mass = np.trapz(C, grid_x, axis=1)
            deviation = np.abs(actual_mass - expected_mass) / (expected_mass + 1e-12)
            max_dev = float(np.max(deviation))
            violation_mass = max_dev > self.epsilon_mass
            checks["mass_conservation"] = {
                "violation": bool(violation_mass),
                "max_relative_error": max_dev,
                "epsilon": self.epsilon_mass,
                "score": float(np.clip(max_dev / (self.epsilon_mass + 1e-9), 0.0, 1.0)),
                "method": "expected_decay",
            }
        else:
            checks["mass_conservation"] = self.check_mass_conservation(C, grid_x, grid_t)

        # 2. BC drift — boundary values at x=0 and x=1 over time
        bc_left  = C[:, 0]
        bc_right = C[:, -1]
        checks["bc_drift"] = self.check_bc_drift(bc_left, bc_right,
                                                  expected_left=0.0,
                                                  expected_right=0.0)

        # 3. PDE residual (pre-computed in the JSON)
        pde_residuals = np.array(output.get("pde_test_residuals", [0.0]), dtype=float)
        checks["pde_residual"] = self.check_pde_residual(pde_residuals)

        # 4. Positivity
        checks["positivity"] = self.check_positivity(C)

        # 5. Symmetry — for 1D diffusion with IC = sin(pi*x) the solution is
        #    symmetric about x=0.5 at all times
        checks["symmetry"] = self.check_symmetry(C, symmetry_axis="x")

        # ------------------------------------------------------------------
        # Aggregate
        # ------------------------------------------------------------------
        violation_flags = {k: v["violation"] for k, v in checks.items()}
        n_violations = sum(violation_flags.values())

        # Compound: 2+ checks flagged
        if n_violations >= 2:
            predicted_type = "compound"
        elif violation_flags["mass_conservation"]:
            predicted_type = "mass_violation"
        elif violation_flags["bc_drift"]:
            predicted_type = "bc_drift"
        elif violation_flags["pde_residual"]:
            predicted_type = "pde_residual"
        elif violation_flags["positivity"]:
            predicted_type = "positivity"
        elif violation_flags["symmetry"]:
            predicted_type = "symmetry"
        else:
            predicted_type = "none"

        overall_pass = n_violations == 0

        # Violation score: mean of individual check scores, weighted to favour
        # the worst offender
        individual_scores = [v["score"] for v in checks.values()]
        violation_score = float(np.clip(
            0.5 * max(individual_scores) + 0.5 * np.mean(individual_scores),
            0.0, 1.0
        ))

        return {
            "id": output_id,
            "overall_pass": bool(overall_pass),
            "violation_score": round(violation_score, 6),
            "predicted_violation_type": predicted_type,
            "n_violations_detected": int(n_violations),
            "checks": checks,
        }

    def score(self, output: dict) -> float:
        """
        Return a scalar violation score in [0, 1].
        0 = fully compliant, 1 = maximally violating.
        """
        result = self.audit(output)
        return result["violation_score"]

    # ------------------------------------------------------------------
    # ViolationReport convenience wrapper
    # ------------------------------------------------------------------

    def audit_report(self, output: dict) -> ViolationReport:
        """Return a ViolationReport dataclass."""
        result = self.audit(output)
        return ViolationReport(
            violation_type=result["predicted_violation_type"],
            detected=not result["overall_pass"],
            severity=result["violation_score"],
            details=result["checks"],
        )


# ---------------------------------------------------------------------------
# --verify CLI
# ---------------------------------------------------------------------------

def _print_table(rows, headers):
    """Print a simple ASCII table."""
    col_widths = [max(len(str(r[i])) for r in ([headers] + rows)) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "  ".join("-" * w for w in col_widths)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(x) for x in row]))


def verify_results(results_path: str) -> int:
    """
    Load results.json, recompute violation scores from stored numpy arrays,
    compare against stored scores.

    Exit code 0 if all scores match within 1e-6.
    Exit code 1 otherwise.
    """
    import os

    with open(results_path, "r") as f:
        stored = json.load(f)

    synthetic_dir = os.path.join(
        os.path.dirname(os.path.abspath(results_path)),
        "synthetic_ai_outputs"
    )

    auditor = PhysicsAuditor(
        epsilon_mass     = stored["metadata"].get("epsilon_mass",        0.05),
        epsilon_bc       = stored["metadata"].get("epsilon_bc",          0.1),
        epsilon_pde      = stored["metadata"].get("epsilon_pde",         0.05),
        epsilon_positivity = stored["metadata"].get("epsilon_positivity",-0.01),
        epsilon_symmetry = stored["metadata"].get("epsilon_symmetry",    0.01),
    )

    rows = []
    all_match = True
    tol = 1e-6

    output_ids = sorted(stored["results"].keys())
    for output_id in output_ids:
        json_path = os.path.join(synthetic_dir, f"{output_id}.json")
        if not os.path.isfile(json_path):
            print(f"WARNING: {json_path} not found — skipping")
            continue

        with open(json_path, "r") as f:
            pinn_output = json.load(f)

        recomputed = auditor.audit(pinn_output)
        stored_score   = stored["results"][output_id]["violation_score"]
        recomputed_score = recomputed["violation_score"]
        diff = abs(stored_score - recomputed_score)
        match = diff <= tol

        if not match:
            all_match = False

        rows.append([
            output_id,
            f"{stored_score:.6f}",
            f"{recomputed_score:.6f}",
            f"{diff:.2e}",
            "OK" if match else "MISMATCH",
        ])

    headers = ["Output ID", "Stored Score", "Recomputed Score", "Diff", "Match"]
    _print_table(rows, headers)

    n_ok       = sum(1 for r in rows if r[-1] == "OK")
    n_mismatch = sum(1 for r in rows if r[-1] == "MISMATCH")
    print()
    print(f"Verified {len(rows)} outputs: {n_ok} OK, {n_mismatch} MISMATCH")

    if all_match:
        print("VERIFICATION PASSED — all scores match within 1e-6")
        return 0
    else:
        print("VERIFICATION FAILED — scores do not match")
        return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Physics Auditor — conservation law checker for PINN outputs"
    )
    parser.add_argument(
        "--verify",
        metavar="RESULTS_JSON",
        help="Verify stored results.json by recomputing all scores",
    )
    args = parser.parse_args()

    if args.verify:
        sys.exit(verify_results(args.verify))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
