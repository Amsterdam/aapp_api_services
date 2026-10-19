---
name: commit-helper
title: Commit Helper
description: Write clear conventional-commit messages from a staged diff. Use when committing changes or when asked to tidy up a commit message.
tags: [git, commits, conventions, pull-request]
version: 1.0.0
---

# Commit Helper

Turn a staged diff into a commit message that explains the change rather than restating it.

## Steps

1. Read the staged changes with `git diff --cached`. If nothing is staged, say so and stop.
2. Work out what the change *does* — the behaviour that differs afterwards, not the files touched.
3. Pick a type from the table in [reference.md](reference.md).
4. Write the subject line: `type(scope): imperative summary`, at most 72 characters, no
   trailing period.
5. Add a body only when the change needs a reason: what was wrong before, why this fix, and any
   consequence a reader would not guess from the diff. The body should be 250 characters or less.
   

## Example

```
fix(auth): refresh the session token before it expires

Tokens were refreshed on the first 401, which logged users out mid-request
on slow connections. Refresh now happens 60s ahead of expiry instead.
```

## Notes

- One commit per logical change. If the diff does two things, say so and suggest a split.
- Never invent an issue number or a co-author.