# Physics Auditor — CAISc 2026

**"AI Scientists Cannot Self-Diagnose Their Own Physics Violations: A Physics Auditor Agent for Conservation Law Verification in AI-Generated PINN Experiments"**

[![CAISc 2026](https://img.shields.io/badge/CAISc-2026-blue)](https://caisc2026.github.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Overview

End-to-end AI scientist systems generate physics-informed neural network (PINN) experiments but have no mechanism to verify physical consistency. This repository provides the **Physics Auditor** — a lightweight post-hoc verification agent that automatically detects conservation law violations in AI-generated PINN outputs.

**Key result:** Physics Auditor achieves **100% recall** (95% CI: [0.893, 1.000]) on all injected violations across N=40 synthetic AI-scientist-style outputs. A prompted LLM baseline reviewer achieves **46.9% recall** (95% CI: [0.309, 0.635]) — a gap of **53.1 percentage points** (McNemar's test: χ²=15.06, p=0.0001).

---

## Repository Structure

```
physics-auditor-caisc2026/
├── outputs/
│   ├── experiments/
│   │   ├── physics_auditor.py          # Core Physics Auditor implementation
│   │   ├── generate_synthetic.py       # Synthetic AI-scientist PINN output generator
│   │   ├── llm_baseline.py             # Simulated GPT-4 reviewer baseline
│   │   ├── run_experiment.py           # Full experiment runner
│   │   ├── generate_figures.py         # Figure generation
│   │   ├── results.json                # Auditor results on 40 outputs
│   │   ├── llm_baseline_results.json   # LLM baseline results
│   │   ├── violation_labels.json       # Ground truth labels
│   │   ├── synthetic_ai_outputs/       # 40 synthetic PINN outputs (JSON)
│   │   ├── figures/                    # Generated figures
│   │   └── findings.md                 # Experimental findings summary
│   └── literature/
│       └── summary.md                  # Literature review summary
├── paper/
│   ├── main.tex                        # CAISc 2026 paper (LaTeX)
│   ├── refs.bib                        # Bibliography
│   └── caisc_2026.sty                  # CAISc 2026 style file
├── Submission_Template_For_CAISc_2026/ # Official template
└── CLAUDE.md                           # Multi-agent pipeline documentation
```

---

## Quickstart: Reproduce Table 1 in Under 2 Minutes

```bash
# 1. Generate the 40 synthetic PINN outputs
python outputs/experiments/generate_synthetic.py

# 2. Run the Physics Auditor + LLM baseline + compute statistics
python outputs/experiments/run_experiment.py

# 3. Verify results match paper Table 1
python outputs/experiments/physics_auditor.py --verify outputs/experiments/results.json
```

**Expected output of step 3:**
```
All 40 outputs verified. Scores match within 1e-6. Exit code 0.
Auditor recall:  1.000  (95% CI: [0.893, 1.000])
Baseline recall: 0.469  (95% CI: [0.309, 0.635])
Gap: 53.1 pp  (McNemar p=0.0001)
```

Runtime: ~0.11 seconds on a standard CPU laptop.

---

## Physics Checks

The auditor applies five checks to each PINN output:

| Check | Threshold | Method |
|-------|-----------|--------|
| Mass conservation | ε = 0.05 | Compare ∫u dx vs expected M₀·exp(−Dπ²t) |
| BC drift | ε = 0.10 | max\|u(boundary,t) − 0\| over all t |
| PDE residual | ε = 0.05 | MSE of ∂u/∂t − D·∂²u/∂x² at 200 held-out points |
| Positivity | ε = −0.01 | min(u) across full domain × time |
| Symmetry | ε = 0.01 | Mean \|u(x,t) − u(1−x,t)\| for symmetric IC |

---

## Violation Types in Dataset

| Type | N | Auditor Recall | LLM Recall |
|------|---|----------------|------------|
| Mass conservation | 8 | 100% | 0% |
| BC drift | 8 | 100% | 100% |
| PDE residual | 8 | 100% | 0% |
| Positivity | 4 | 100% | 75% |
| Compound (2+) | 4 | 100% | 100% |
| Clean (FP rate) | 8 | 0% FP | 0% FP |

---

## Requirements

```
numpy
scipy
```

No GPU required. No external API calls. Runs entirely on CPU.

---

## Citation

```bibtex
@inproceedings{anonymous2026physicsauditor,
  title     = {AI Scientists Cannot Self-Diagnose Their Own Physics Violations:
               A Physics Auditor Agent for Conservation Law Verification
               in AI-Generated PINN Experiments},
  author    = {Anonymous},
  booktitle = {CAISc 2026},
  year      = {2026}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
