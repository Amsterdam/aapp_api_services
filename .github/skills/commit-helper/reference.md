# Conventional commit types

This file exists to demonstrate a skill with supporting files: it is bundled into the
downloadable `.skill` archive alongside `SKILL.md`, and the agent reads it only when the skill
body points at it.

| Type       | Use for                                                        |
| ---------- | -------------------------------------------------------------- |
| `feat`     | A new capability visible to a user                              |
| `fix`      | A bug fix                                                       |
| `docs`     | Documentation only                                              |
| `refactor` | A change that neither fixes a bug nor adds a feature            |
| `perf`     | A change that improves performance                              |
| `test`     | Adding or correcting tests                                      |
| `build`    | Build system, dependencies, packaging                           |
| `ci`       | CI configuration and workflows                                  |
| `chore`    | Anything else that does not change source behaviour             |

## Scope

The scope is the area of the codebase the change belongs to — a module, a package, a surface.
Leave it out rather than inventing one: `fix: ...` is better than `fix(misc): ...`.

## Breaking changes

Append `!` after the type and explain the break in the body:

```
feat(api)!: require an explicit region on every client

Callers that relied on the implicit "us-east-1" default must now pass one.
```