# PM Automation Feature Roadmap (z5d-prime-predictor)

## Phase 1: Baseline (Complete ✓)

**Objective:** Run a prompt chain that produces daily PM reports without manual setup.

**What Exists Now:**
- Task chain 00→01→02→03 executes end-to-end.
- Wrapper script pre-approves required tools.
- Reports post to a single "PM Agent State" issue.

**Limitation:** Reports are factual but light on insight, trend, and prioritization.

---

## Phase 2: Insightful, Actionable PM (Next)

Guiding principle: small, testable increments that add commentary, trend spotting, and decision support for this project (performance + release readiness on Apple Silicon).

### Candidate Increments

**R1: Bench/Build Sentinel**
- Summarize latest bench artifacts (CSV/MD) and flag deltas/regressions vs previous run.
- Acceptance: Report shows top deltas and highlights suspected causes (if present in notes).

**R2: Release Readiness Scorecard**
- Track checklist (build reproducibility, binaries/artifacts present, docs updated, version bump plan).
- Acceptance: Include a simple score (e.g., 0–100) with top 3 gaps.

**R3: Dependency & Env Drift Watcher**
- Detect changes to MPFR/GMP versions or build flags; warn if diverging from expected baselines.
- Acceptance: Report lists current vs last-known versions and potential impact.

**R4: Directional PR/Issue Summaries**
- Generate short recommendations per active PR/issue (merge risk, next step, owner/ask).
- Acceptance: At least one actionable recommendation per active item.

**R5: Weekly Trajectory Narrative**
- Aggregate daily reports into a weekly trend (velocity, stability, risk movement) with a brief narrative.
- Acceptance: Weekly comment posted to state issue with top trends and next bets.

**R6: Notification Outputs (Optional)**
- Push PM report to chat/email; configurable destinations.
- Acceptance: One additional delivery channel works end-to-end.

---

## Success Criteria
- Each increment is independently testable and can be reverted cleanly.
- Adds measurable value: faster decision-making, earlier risk surfacing, or clearer next steps.
- Keeps prompts concise; commentary stays within a few sentences per section.

---

## Next Steps
1. Pick R1 or R4 as the first increment (low effort, immediate value).
2. Define minimal data needed for that increment (bench paths, expected versions, owners).
3. Implement and validate via the existing task chain and wrapper script.
4. Iterate on scoring/formatting after one cycle of real output.

---

**Roadmap Status:** Draft (2025-11-22)
**Owner:** PM Automation for z5d-prime-predictor
**Stakeholders:** Project maintainers
