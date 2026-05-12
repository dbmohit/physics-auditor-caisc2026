# Supervisor 10-Item CAISc Checklist — Iteration 1
# Date: 2026-05-10
# Paper: paper/main.tex
# Reviewer: supervisor (Claude)

---

## Checklist Results

### Item 1 — META-FRAMING
**Status: [PASS]**

Sentence 1 of the abstract reads verbatim: "We present the first systematic study of AI scientists
critiquing AI-generated science: a Physics Auditor agent that automatically detects conservation
law violations in PINN experiments produced by end-to-end AI research systems, revealing that
state-of-the-art AI scientists generate physically inconsistent results at high rates that neither
their built-in AI reviewers nor prompted LLM baselines reliably detect."

The identical sentence opens Section 1 (Introduction), line 80-86 of main.tex. Both
placements satisfy dispatch Fix 1. The appendix AI Involvement Statement reinforces
the meta-frame explicitly: "This paper is itself an instance of the phenomenon it studies."

---

### Item 2 — THREE-BEAT STORY
**Status: [PASS]**

All six sections map cleanly to the three beats:

- PROBLEM (Beat 1): Section 1 (Introduction) establishes the structural gap — AI scientists
  generate PINN outputs with no conservation checking; Section 2 (Related Work) reviews the
  evidence and closes with the verbatim gap statement "We fill this gap with the Physics Auditor."
  Both sections serve Beat 1 exclusively.

- EVIDENCE (Beat 2): Section 3 (Physics Auditor) describes the system under test; Section 4
  (Experiments) delivers the quantitative evidence — Table 1 (main result), Table 2 (per-type),
  statistical significance tests, and two case studies. Both sections serve Beat 2 exclusively.

- SOLUTION + LIMITS (Beat 3): Section 5 (Discussion) explains why LLMs structurally cannot
  detect physics violations and argues for post-hoc auditing as a pipeline component; Section 6
  (Limitations and Broader Impacts) covers check coverage, synthetic outputs, single PDE,
  single baseline, positive/negative impacts, and ethics statement. Both sections serve
  Beat 3 exclusively.

No section crosses beat boundaries or introduces material that belongs to a different beat.

---

### Item 3 — VERIFIABLE ARTIFACT
**Status: [PASS]**

Abstract final sentence (lines 69-71): "All violation scores are auto-computable from the
released dataset; any reviewer can re-run the Physics Auditor on the 40 test outputs and
reproduce Table 1 in under two minutes on a standard laptop." — verbatim from dispatch.

Section 4.1 (lines 438-448): "This paper targets the CAISc 2026 Verifiable Track. The
verification artifact is outputs/experiments/results.json, which contains per-output
violation scores for all 40 test cases. Table 1 is generated deterministically from this
file by running: python outputs/experiments/physics_auditor.py --verify results.json"
— verbatim from dispatch.

The Reproducibility Checklist in the appendix (Item 4) also specifies the exact command
with expected exit-code-0 behavior and tolerance of 1e-6. Three separate placements
satisfy the verifiable track requirement.

---

### Item 4 — HEADLINE NUMBERS
**Status: [PASS]**

All four required numbers appear with exact values, consistently:

| Number | Required | Found in abstract | Found in Sec 4.2 | Found in Table 1 |
|--------|----------|-------------------|------------------|------------------|
| Auditor recall | 100% | line 61 | line 498 | Table 1 row 1 |
| Baseline recall | 46.9% | line 63 | line 500 | Table 1 row 2 |
| Gap | 53.1 pp | line 64 | line 501 | Table caption |
| p-value | p=0.0001 | line 64 | line 502 | Table caption |

The chi-squared statistic (chi^2=15.06) is present in both the abstract and Table 1 caption.
The 95% CIs ([0.893, 1.000] and [0.309, 0.635]) are consistent across the abstract, Table 1,
and Section 4.3. No discrepancies found between findings.md source values and paper values.

---

### Item 5 — GAP STATEMENT
**Status: [PASS]**

The gap statement appears as the final named paragraph of Section 2 (Related Work), under
the heading "\paragraph{Gap statement.}" at lines 215-247 of main.tex.

The paragraph begins: "Despite substantial progress in both AI scientist systems and PINN
research, a critical verification gap persists at their intersection..." and ends: "We fill
this gap with the Physics Auditor." — matching the verbatim-ready text approved in
review_r1.md Part 1, criterion R7.

The placement is correct: it is the last paragraph before Section 3 begins. It cites 10
sources as required. The verbatim instruction from dispatch ("insert gap statement as final
paragraph of Related Work") is satisfied.

---

### Item 6 — TWO BLIND SPOTS
**Status: [PASS]**

Both structural blind spots are named, quantified, and mechanistically explained in
Section 4.3 (Per-Type Analysis), under the heading "Structural blind spots (0% LLM recall)":

Mass non-conservation (0% LLM recall): Explained at lines 540-551. The LLM receives total
mass at t=0 and t=T. The growing factor (1+0.05t) produces only 5% mass increase.
"Distinguishing this from normal decay requires computing the expected curve M(t) = M_0
e^{-D*pi^2*t} and comparing it to the observed trajectory. An LLM reading summary
statistics cannot perform this computation."

PDE residual violations (0% LLM recall): Explained at lines 553-562. Wrong-diffusivity
outputs are smooth and exhibit physical decay. "Detecting this requires computing r = du/dt -
D*d^2u/dx^2 at interior test points — impossible from summary statistics."

Both blind spots are also named in the abstract (line 65-67), the Introduction contributions
list (lines 130-132), and the Discussion paragraph "Why LLM reviewers miss physics violations."
Per-type Table 2 shows the 0% values explicitly for both types.

---

### Item 7 — ANONYMIZATION
**Status: [PASS]**

Author field: "\author{\textbf{Anonymous}\\\textbf{Anonymous Institution}}" (lines 33-34).
No real author names, institution names, email addresses, or acknowledgements appear in
the paper body.

The AI Involvement Statement in the appendix lists agent models (Claude, Gemini CLI,
Codex CLI) without naming any human contributors or institutions.

One item requires monitoring: the TODO-VERIFY comments in refs.bib (e.g., "TODO-VERIFY:
confirm arXiv ID") do not reveal author identity but do reveal that the coder used
placeholder arXiv IDs for Lu2025AIScientistV2, Bai2024ScientificLLM, and
Tyser2024AutomatedReview (entries show arXiv:2504.XXXXX and arXiv:2406.XXXXX). These
placeholder IDs are a camera-ready risk (a reviewer who looks up the ID will get no result)
but are not an anonymization failure — they are known P1-C items from review_r1.md.

**Verdict: [PASS] for anonymization. The placeholder arXiv IDs are a P1-C citation
verification issue, not an identity disclosure issue.**

---

### Item 8 — PAGE LIMIT
**Status: [WARN]**

The paper uses \documentclass[10pt,twocolumn]{article} with 0.75in margins, matching
CAISc formatting. Estimating body length from section content:

- Abstract: ~140 words (~0.25 col)
- Section 1 (Introduction): ~440 words + 3-item enumeration (~0.9 col)
- Section 2 (Related Work): ~580 words (~1.15 col)
- Section 3 (Physics Auditor): ~560 words + 5 equations + Table 1 (tab:checks) (~1.8 col)
- Section 4 (Experiments): ~680 words + Table 2 (tab:setup) + Table 3 (tab:main) +
  Table 4 (tab:pertype) + verbatim block (~2.5 col)
- Section 5 (Discussion): ~360 words (~0.75 col)
- Section 6 (Limitations): ~310 words (~0.65 col)

Total body estimate: ~3070 words + 4 tables + 5 equations
At 10pt twocolumn 0.75in margins: approximately 450 words per column, 900 per page.
Estimated body: 3070 / 900 = ~3.4 pages of text, plus tables, figures, equations.
With tables and equations: estimated 5.5–7.0 pages total body.

This is within the 8-page limit, but the estimate carries uncertainty of ~0.5 pages.

**WARN: A compiled PDF page count is needed to confirm. Phase 6b (page count check)
must be completed before submission. If figures (referenced but not shown in the .tex
source) are added, the count could rise. The current estimate is SAFE but unconfirmed.**

The appendix (AI Involvement Statement + Reproducibility Checklist + LLM Baseline Prompt)
is correctly placed after \appendix and does not count toward the 8-page body limit,
assuming CAISc allows unlimited appendix pages (standard for workshop papers).

---

### Item 9 — AI INVOLVEMENT STATEMENT
**Status: [PASS]**

The appendix contains a dedicated "AI Involvement Statement" section (lines 723-746)
with a four-row table listing:
- Supervisor / Claude / Orchestration, dispatch, review
- Researcher / Gemini CLI / Literature survey (13 papers)
- Coder / Codex CLI / Auditor code + experiments
- Writer / Claude / This LaTeX document

The statement explicitly declares: "No human wrote prose, code, or experiment results"
and "Human involvement: project prompt and initial task specification were provided by
a human principal investigator."

This satisfies both the CAISc AI Involvement requirement and the meta-framing imperative.

---

### Item 10 — REPRODUCIBILITY CHECKLIST
**Status: [PASS]**

The appendix contains a 10-item "Reproducibility Checklist" (lines 749-807) covering:
1. Claims — all three claims with exact numbers
2. Limitations — scope, single PDE, synthetic outputs, single baseline
3. Theory — N/A, empirical paper
4. Reproducibility — epsilons, 40 outputs, verification command, tolerance
5. Open access — anonymous repo link noted as TODO (P1-B) with placeholder text
6. Experimental details — problem parameters, baseline prompt file, hardware
7. Statistical significance — McNemar + Wilson CIs, with P1-A TODO for per-type CIs
8. Compute — 0.11s total, 2.8ms/output, CPU-only
9. Ethics — synthetic outputs, no misrepresentation
10. Broader impacts — cross-referenced to Section 6

Item 5 has a TODO placeholder for the anonymous repo URL (P1-B), and Item 7 has a TODO
for per-violation-type Wilson CIs (P1-A). Both were known P1 items from review_r1.md and
do not constitute a checklist failure — the framework is in place.

---

## Summary

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | META-FRAMING | [PASS] | Verbatim dispatch sentence in abstract line 46 and intro line 80 |
| 2 | THREE-BEAT STORY | [PASS] | All 6 sections map to Problem/Evidence/Solution+Limits without crossing |
| 3 | VERIFIABLE ARTIFACT | [PASS] | --verify command in abstract final sentence, Section 4.1, and Appendix Item 4 |
| 4 | HEADLINE NUMBERS | [PASS] | 100%/46.9%/53.1pp/p=0.0001 consistent across abstract, Sec 4.2, and Table 1 |
| 5 | GAP STATEMENT | [PASS] | Verbatim gap statement is final named paragraph of Section 2 (lines 215-247) |
| 6 | TWO BLIND SPOTS | [PASS] | Mass=0% and PDE=0% named, quantified, and mechanistically explained in Sec 4.3 |
| 7 | ANONYMIZATION | [PASS] | Author/institution anonymous; placeholder arXiv IDs are P1-C citation risk, not identity risk |
| 8 | PAGE LIMIT | [WARN] | Estimated 5.5-7.0 body pages — within 8-page limit but unconfirmed until compiled PDF |
| 9 | AI INVOLVEMENT | [PASS] | Appendix table with 4 agents, models, and contributions; human role stated |
| 10 | REPRODUCIBILITY | [PASS] | 10-item appendix checklist with two flagged TODOs (P1-A, P1-B) known from review_r1.md |

**PASS count: 9**
**WARN count: 1 (Item 8 — page limit unconfirmed)**
**FAIL count: 0**

---

## Verdict

**READY FOR SUBMISSION** (conditional on resolving outstanding P1 items before camera-ready)

0 FAIL items. 1 WARN item (page limit — requires compiled PDF, not a blocking failure on
the draft itself). This meets the threshold of 0 FAIL and <= 2 WARN.

### Outstanding items before camera-ready submission (Phase 6):

**P1-A** (Item 10 / Checklist Item 7): Add per-violation-type Wilson 95% CIs to Table 2
(tab:pertype) and Appendix Reproducibility Item 7. Coder must compute these.

**P1-B** (Item 10 / Checklist Item 5): Insert anonymous.4open.science URL in Reproducibility
Item 5 and optionally in Section 4.1. Coder must create the anonymous repo in Phase 6d.

**P1-C** (Item 7 / refs.bib): Verify 7 placeholder/unconfirmed citations before camera-ready:
Lu2025AIScientistV2, Rathore2024, Bai2024ScientificLLM, Tyser2024AutomatedReview,
Gao2024ReviewerBias, Daw2022MitigatingPropagation, Cuomo2022ScientificML.

**P1-D** (Item 6): Compound violation narrative is present in Section 4.3 — satisfies
the dispatch requirement. No further action needed.

**P1-E** (Item 6): Symmetry check scope limitation is explicitly stated in Section 3,
Check 5, lines 336-339: "applicable to symmetric problems only." Satisfies P1-E.
No further action needed.

**WARN-8** (Item 8): Compile paper/main.tex to PDF and confirm body <= 8 pages.
This is Phase 6b in the pipeline. If figures are inserted, re-check.

### Next action
Phase 5b: Revision round — coder addresses P1-A (per-type CIs) + P1-C (citation verification).
Phase 6a: Anonymization audit using grep command.
Phase 6b: Compile PDF and confirm page count <= 8 pages.
Phase 6c: Confirm verification artifact (physics_auditor.py --verify exits 0).
Phase 6d: Create anonymous repo on anonymous.4open.science.
Phase 7: Submit to OpenReview by May 15, 2026.

---

*Checklist written by supervisor — 2026-05-10 — Iteration 1*
