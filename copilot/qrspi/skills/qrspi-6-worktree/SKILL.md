---
name: qrspi-6-worktree
description: "QRSPI phase 6: Create an isolated git worktree for implementation. Only use when the user explicitly invokes this skill by name."
---
# Worktree — Isolate the Implementation

`<dir>` is the artifact directory passed with this skill, for example `thoughts/qrspi/<id>/`. If none was given, ask the user for it before doing anything else.

Start a fresh session for each phase when you can; each phase reads only its own input artifacts.

Create a git worktree so implementation happens on an isolated branch without affecting your main working tree.

## Input

The artifact directory is `<dir>`.

## Process

1. **Determine identifiers** from the artifact directory name:
   - Branch name: derive from the directory name (e.g., `ENG-1234-description` or `2026-03-29-new-feature`)
   - Repo name: detect from `basename $(git rev-parse --show-toplevel)`
   - Worktree path: `~/wt/<repo-name>/<branch-name>`

2. **Create the worktree:**
   ```
   git worktree add ~/wt/<repo-name>/<branch-name> -b <branch-name>
   ```

3. **Confirm with the user** before executing:
   ```
   Ready to create worktree:

   Worktree: ~/wt/<repo-name>/<branch-name>
   Branch: <branch-name>
   Plan: <dir>/plan.md

   To implement, run from the worktree:
     /qrspi-7-implement <dir>

   Proceed?
   ```

4. **Create the worktree** after user confirms.

5. **Copy QRSPI artifacts** to the worktree. Untracked files from the main tree do not appear in worktrees:
   ```
   cp -r <artifact-directory> ~/wt/<repo-name>/<branch-name>/<artifact-directory>
   ```

## Output

- Git worktree created at `~/wt/<repo-name>/<branch-name>`
- QRSPI artifacts copied to the worktree
- Tell the user the worktree path and how to start implementation

## Rules

- Always confirm before creating the worktree.
- Worktrees do not share untracked files with the main tree. Always copy the artifact directory after creating the worktree.
- Do not start implementation. That's a separate phase with a separate context window.

## When to Go Back

If the plan doesn't exist yet at `<dir>/plan.md`, tell the user to run `/qrspi-5-plan` first.
