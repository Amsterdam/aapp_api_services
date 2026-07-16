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
- `verdict`: one of `approved` | `blocked`
- `findings`: array, may be empty only for genuinely trivial changes
- `technical_risks`
- `next_step`

Each entry in `findings` must include:

- `severity`: one of `critical` | `major` | `minor` | `nit`
- `category`: one of `correctness` | `edge_case` | `regression_risk` | `security` | `test_coverage` | `naming_readability` | `duplication_design` | `consistency` | `documentation`
- `location`: file and line/hunk reference, or symbol name if line numbers are unstable
- `description`: what is wrong
- `impact`: what concretely breaks or degrades, and under what conditions — not just "could be improved"
- `evidence`: see Evidence Rule in reviewer agent definition below

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
- `coverage_exercised`: array of checklist categories actually exercised, each with a brief note on what was checked (see Coverage Rule below)
- `untested_paths`: array of things considered but not verified, each with a reason (see Untested Paths Rule below)
- `result`: one of `pass` | `fail` | `partial_confidence`
- `defects`: array, required to be non-empty if `result` is `fail`
- `test_quality_notes`: array, may be empty only when existing/new tests were inspected and found to assert meaningful outcomes (see Test Quality Rule below)
- `residual_risk`: array, may be empty only for genuinely trivial changes (see Residual Risk Rule below)
- `resulting_git_hash`
- `next_step`

Each entry in `defects` must include:

- `severity`: one of `critical` | `major` | `minor`
- `category`: one of `happy_path` | `edge_case` | `error_handling` | `regression_risk` | `concurrency_ordering` | `contract_api_surface` | `test_quality`
- `description`: what is wrong
- `impact`: what concretely breaks, and under what conditions
- `evidence`: the specific test run, command output, or file/line inspected that supports the defect — not an assumption

Validation note:

- Tester responses are valid only when `schema` is exactly `H7 Test Result`.
- If a non-`H7` payload is returned to a test request, the Orchestrator must reject it as schema-invalid and request a corrected `H7 Test Result` before progressing.
- A payload missing `coverage_exercised` or `untested_paths`, or containing a `defects` array that lacks `severity`/`category`/`evidence` on any entry, must be treated as schema-invalid in the same way and sent back for correction.