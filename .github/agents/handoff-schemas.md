# Handoff Schemas

These named contracts are required by the Orchestrator. Every major handoff must declare the matching `schema` value and include all required fields.

## Git Lineage Rules

- `original_git_hash` is the repository `HEAD` captured by the Orchestrator before the first subagent for the work item starts.
- `git_history_context` summarizes the relevant commits from `original_git_hash` to the current `HEAD`. Use that git history as the provenance record for the work item.
- Any Developer or Tester session that changes repository content must end with a commit whose subject starts with the subagent name.

## Schema Catalog

- `H0 Story Planning Request`: Orchestrator to Story Plan planning handoff.
- `H1 Story Planning Result`: Story Plan back to Orchestrator planning result.
- `H2 Developer Request`: Orchestrator to Developer implementation handoff.
- `H3 Developer Result`: Developer back to Orchestrator implementation result.
- `H4 Review Request`: Orchestrator to Reviewer blinded review handoff.
- `H5 Review Result`: Reviewer back to Orchestrator review result.
- `H6 Test Request`: Orchestrator to Tester blinded validation handoff.
- `H7 Test Result`: Tester back to Orchestrator test result.

## H0 Story Planning Request

Use for the approved planning handoff from Orchestrator to Story Plan.

Required fields:

- `schema`: `H0 Story Planning Request`
- `original_story`
- `planning_goal`
- `planning_constraints`

## H1 Story Planning Result

Use for the Story Plan handoff back to Orchestrator after it has created or updated `plan.md`.

Required fields:

- `schema`: `H1 Story Planning Result`
- `plan_status`
- `plan_md_file`
- `plan_summary`
- `open_questions`
- `assumptions_recorded`
- `known_risks`

## H2 Developer Request

Use for the approved implementation handoff from Orchestrator to Developer.

Required fields:

- `schema`: `H2 Developer Request`
- `original_work_item`
- `plan_md_file_location`
- `original_git_hash`
- `relevant_codebase_context`
- `implementation_constraints`

## H3 Developer Result

Use for the Developer handoff back to Orchestrator after implementation or rework.

Required fields:

- `schema`: `H3 Developer Result`
- `changes_made`
- `unit_tests_added_or_updated`
- `validations_run`
- `assumptions`
- `open_risks`
- `resulting_git_hash`

## H4 Review Request

Use for the blinded review handoff from Orchestrator to Reviewer.

Required fields:

- `schema`: `H4 Review Request`
- `original_work_item`
- `original_git_hash`
- `git_history_context`
- `review_focus`

## H5 Review Result

Use for the Reviewer handoff back to Orchestrator.

Required fields:

- `schema`: `H5 Review Result`
- `verdict`: one of `ready_for_testing` | `blocked`
- `blocking_findings`: array, may be empty only if `verdict` is `ready_for_testing`
- `non_blocking_findings`: array, may be empty only for genuinely trivial changes — see Non-Blocking Findings Rule below
- `technical_risks`
- `next_step`

Each entry in `blocking_findings` and `non_blocking_findings` must include:

- `severity`: one of `critical` | `major` | `minor` | `nit`
- `category`: one of `correctness` | `edge_case` | `regression_risk` | `security` | `test_coverage` | `naming_readability` | `duplication_design` | `consistency` | `documentation`
- `location`: file and line/hunk reference, or symbol name if line numbers are unstable
- `description`: what is wrong
- `impact`: what concretely breaks or degrades, and under what conditions — not just "could be improved"
- `evidence`: see Evidence Rule below

Non-Blocking Findings Rule:

- `non_blocking_findings` being empty is only acceptable when the diff is genuinely trivial (e.g. a one-line config value, a typo fix, a pure rename with no other changes). For any other change, an empty `non_blocking_findings` array is treated as a signal the review was incomplete, not as evidence the code was flawless. The Reviewer should have re-checked the diff before submitting such a result.
- `non_blocking_findings` must never be used to bury something that should actually block. If in doubt about severity, escalate to `blocking_findings`.

Evidence Rule (applies to all finding categories, not just test_coverage):

- Every finding must be traceable to something the Reviewer actually inspected — a specific file/line, a `git log`/`git show` output, or an explicit repository search — not an assumption about how the codebase "probably" works.
- Findings that claim "missing coverage" must cite either a failed/absent test run or explicit repository search evidence that no equivalent test exists outside the changed diff. If equivalent coverage is present elsewhere, mark as residual risk or suggestion instead of a blocking defect.
- Findings that claim "duplication" or "inconsistency with existing patterns" must cite the specific other location(s) being duplicated or diverged from. A duplication/consistency finding without a cited counterpart is a suggestion at most, not a defect.
- Findings that claim "regression risk" must cite the caller(s) or usage site(s) affected. A regression-risk finding without an identified affected caller must be labeled a residual risk, not a blocking defect.
- If evidence cannot be produced for a finding, downgrade it: move it from `blocking_findings` to `non_blocking_findings`, or from a defect to a note in `technical_risks`, rather than dropping it or asserting it unsupported.

## H6 Test Request

Use for the blinded validation handoff from Orchestrator to Tester.

Required fields:

- `schema`: `H6 Test Request`
- `original_work_item`
- `original_git_hash`
- `git_history_context`
- `test_focus`

## H7 Test Result

Use for the Tester handoff back to Orchestrator.

Required fields:

- `schema`: `H7 Test Result`
- `coverage_exercised`
- `result`
- `defects`
- `residual_risk`
- `resulting_git_hash`
- `next_step`

Validation note:

- Tester responses are valid only when `schema` is exactly `H7 Test Result`.
- If a non-`H7` payload is returned to a test request, the Orchestrator must reject it as schema-invalid and request a corrected `H7 Test Result` before progressing.
