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

- `schema`: `H0 Story Planning Result`
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
- `verdict`
- `findings`
- `technical_risks`
- `next_step`

Review evidence rule:

- Findings that claim "missing coverage" must cite either a failed/absent test run or explicit repository search evidence that no equivalent test exists outside the changed diff.
- If equivalent coverage is present elsewhere, mark as residual risk or suggestion instead of a blocking defect.

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
