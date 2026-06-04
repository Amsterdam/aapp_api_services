# Handoff Schemas

These named contracts are required by the Orchestrator. Every major handoff must declare the matching `schema` value and include all required fields.

## Global Required Fields

- `schema`
- `work_item_id`
- `source_role`
- `target_role`

## Schema Catalog

- `H1 Canonical Work Item Brief`: Orchestrator canonical record and downstream source brief.
- `H2 Developer Request`: Orchestrator to Developer implementation handoff.
- `H3 Developer Result`: Developer back to Orchestrator implementation result.
- `H4 Review Request`: Orchestrator to Reviewer blinded review handoff.
- `H5 Review Result`: Reviewer back to Orchestrator review result.
- `H6 Rework Request`: Orchestrator to Developer rework handoff after review or testing.
- `H7 Test Request`: Orchestrator to Tester blinded validation handoff.
- `H8 Test Result`: Tester back to Orchestrator test result.

## H1 Canonical Work Item Brief

Use for the Orchestrator's canonical work item record and as the source for downstream handoffs.

Required fields:

- `schema`: `H1 Canonical Work Item Brief`
- `title`
- `desired_outcome`
- `constraints`
- `acceptance_direction`
- `priority`
- `non_goals`
- `open_questions`
- `known_risks`
- `next_validation_step`

## H2 Developer Request

Use for the approved implementation handoff from Orchestrator to Developer.

Required fields:

- `schema`: `H2 Developer Request`
- `canonical_work_item`
- `relevant_codebase_context`
- `implementation_constraints`
- `next_validation_step`

## H3 Developer Result

Use for the Developer handoff back to Orchestrator after implementation or rework.

Required fields:

- `schema`: `H3 Developer Result`
- `changes_made`
- `unit_tests_added_or_updated`
- `validations_run`
- `assumptions`
- `open_risks`
- `suggested_next_step`

## H4 Review Request

Use for the blinded review handoff from Orchestrator to Reviewer.

Required fields:

- `schema`: `H4 Review Request`
- `original_work_item`
- `git_status_diff`
- `review_focus`
- `next_validation_step`

## H5 Review Result

Use for the Reviewer handoff back to Orchestrator.

Required fields:

- `schema`: `H5 Review Result`
- `verdict`
- `findings`
- `technical_risks`
- `test_focus`
- `next_step`

## H6 Rework Request

Use when Orchestrator routes blocking review or test findings back to Developer.

Required fields:

- `schema`: `H6 Rework Request`
- `original_work_item`
- `blocking_findings`
- `required_rework`
- `implementation_constraints`
- `next_validation_step`

## H7 Test Request

Use for the blinded validation handoff from Orchestrator to Tester.

Required fields:

- `schema`: `H7 Test Request`
- `original_work_item`
- `artifact_under_test`
- `test_focus`
- `next_validation_step`

## H8 Test Result

Use for the Tester handoff back to Orchestrator.

Required fields:

- `schema`: `H8 Test Result`
- `coverage_exercised`
- `result`
- `defects`
- `residual_risk`
- `next_step`
