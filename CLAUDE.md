# CAISc 2026 — Physics Auditor Paper
# "AI Scientists Cannot Self-Diagnose Their Own Physics Violations:
#  A Physics Auditor Agent for Conservation Law Verification in AI-Generated PINN Science"

## READ FIRST — EVERY SESSION
```bash
cat outputs/progress.md
```
Resume from RESUME BLOCK. Never redo [PASS] work.

---

## The Core Idea
End-to-end AI scientist systems (AI Scientist v2, Agent Laboratory) generate
PINN experiments but have zero mechanism to verify physical consistency.
They routinely produce results that violate conservation laws — and neither
the AI author nor AI reviewer catches it.

We build a lightweight "Physics Auditor" agent that:
1. Wraps around any AI-generated PINN experiment
2. Automatically flags conservation law violations
3. Reports mass/energy non-conservation and BC drift quantitatively
4. Shows how often AI scientists produce physically inconsistent science

## Agent Roles
| Agent | Model | Task |
|-------|-------|------|
| supervisor | Claude | Orchestrate + review + submission gatekeeper |
| researcher | Gemini CLI | Literature on AI scientist systems, PINN failures, conservation laws |
| coder | Codex CLI | Physics Auditor implementation + experiments on AI-generated outputs |
| writer | Claude | LaTeX paper in CAISc 2026 template |

---

## Dispatch Rules

### PARALLEL
- researcher (literature) + coder (auditor scaffold) — different folders
- writer drafting + supervisor reviewing previous section

### SEQUENTIAL
1. supervisor reads progress.md → task breakdown
2. researcher + coder in parallel
3. supervisor reviews both → checklist
4. writer drafts from approved content
5. supervisor runs 10-item CAISc checklist
6. revise → repeat until all [PASS]
7. supervisor runs submission gatekeeper
8. submit OpenReview by May 15 2026

---

## File Ownership
| Path | Owner |
|------|-------|
| outputs/literature/ | researcher |
| outputs/experiments/ | coder |
| outputs/review/ | reviewer |
| paper/ | writer |
| outputs/progress.md | ALL — append only |
| outputs/supervisor/ | supervisor |

---

## Core Research Details

### The Experiment Design
1. Take AI-generated PINN outputs (from AI Scientist v2 or Agent Laboratory)
   OR generate synthetic "AI scientist outputs" with known violations
2. Run Physics Auditor on each output
3. Report: violation rate, violation type, severity
4. Show: AI reviewer (baseline LLM) misses these violations
5. Show: Physics Auditor catches them all

### Physics Checks the Auditor Runs
- Mass conservation: |∫C dΩ(t) - ∫C dΩ(0)| / ∫C dΩ(0) < ε
- Energy conservation (if applicable)
- Boundary condition drift: max residual at boundaries over time
- PDE residual at test points (not training points)
- Positivity constraint violations (concentration < 0)
- Symmetry violations (if problem has known symmetry)

### Verifiable Artifact
Conservation error is auto-computable — perfect for CAISc verifiable track.
Given AI-generated output → Auditor flags → checkable against ground truth.

### Deadline
May 15 2026 — 19 days from project start.

---

## 19-Day Timeline
| Days | Task | Agents |
|------|------|--------|
| 1-2 | Literature + Auditor scaffold | researcher + coder parallel |
| 3-4 | Generate/collect AI-generated PINN outputs | coder |
| 5 | Implement all physics checks | coder |
| 6 | Run auditor on AI outputs, collect violation stats | coder |
| 7 | Supervisor review R1 | supervisor |
| 8-10 | Draft Sections 1-4 | writer |
| 11-12 | Draft Sections 5-6 + checklists | writer |
| 13 | Supervisor checklist review | supervisor |
| 14-15 | Revision round | all |
| 16 | Anonymization + page count | supervisor |
| 17 | Repo setup (anonymous) | coder |
| 18 | Submit OpenReview | supervisor |
| 19 | Buffer | all |
