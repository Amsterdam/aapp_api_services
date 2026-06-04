# Custom Agents

This folder contains the concrete agent definitions for the AI delivery workflow.

## Agent Set

- `agent-orchestration-specialist.agent.md` is the agent-design specialist for creating and refining sub-agents, prompt boundaries, and orchestration behavior in this repository.
- `product-owner.agent.md` is the Product Owner support agent that helps the human Product Owner structure briefs and decisions without replacing final human authority.
- `orchestrator.agent.md` is the primary entry point and the only agent intended for direct user invocation.
- `planner.agent.md` is a conditional clarification agent for unclear or risky work items.
- `developer.agent.md` is the implementation agent for approved work items.
- `reviewer.agent.md` is the blinded technical review agent.
- `tester.agent.md` is the blinded behavioral validation agent.
- `ui-ux-designer.agent.md` is an advisory UX agent outside the default delivery loop.

## Operating Intent

- Keep the human Product Owner as the final authority even though a Product Owner support agent exists.
- Route every work item through the same core delivery workflow.
- Route specialist collaboration through the Orchestrator.
- Keep Reviewer and Tester blinded from upstream reasoning.
- Keep agent-creation work focused in the Agent Orchestration Specialist instead of scattering orchestration edits across unrelated agents.

## Lean Workflow

1. Product Owner intent becomes a work item or user story.
2. The Orchestrator restates it as one canonical brief.
3. Planner is activated only when direct implementation would force guessing.
4. Developer implements the full approved work item.
5. Reviewer performs a blinded technical review and may route rework back to Developer through the Orchestrator.
6. Tester performs blinded behavioral validation and may route rework back to Developer through the Orchestrator.
7. Orchestrator assembles the result and returns a recommendation to the human Product Owner.

## Source Of Truth

- The Orchestrator owns the canonical brief for each work item.
- Agent definitions in this folder are now the primary source of role behavior and workflow rules.
- Named handoff schemas in `handoff-schemas.md`, enforced agent response templates, and hook-based enforcement or orchestration automation are required parts of the workflow.
- The human Product Owner remains the final authority on value, scope trade-offs, and release approval.

## Required Contracts

- named handoff schemas in `handoff-schemas.md`
- enforced response templates for agents
- hook-based enforcement
