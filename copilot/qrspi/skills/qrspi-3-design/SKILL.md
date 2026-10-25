---
name: qrspi-3-design
description: "QRSPI phase 3: Design discussion — align on where we are going before planning how. Only use when the user explicitly invokes this skill by name."
---
# Design — Where Are We Going?

`<dir>` is the artifact directory passed with this skill, for example `thoughts/qrspi/<id>/`. If none was given, ask the user for it before doing anything else.

Start a fresh session for each phase when you can; each phase reads only its own input artifacts.

Create a ~200-line design document that captures the current state, desired end state, design decisions, and patterns to follow. This is the **lowest-cost point for direction changes** — get alignment here before investing in detailed planning.

## Input

Read `<dir>/task.md`, `<dir>/questions.md`, and `<dir>/research.md`.

## Process

1. **Read all three artifacts fully.** `task.md` tells you what we're building. `research.md` tells you what exists. Understand both before proceeding.

2. **Targeted exploration**: If the research revealed areas that need deeper investigation for design decisions, spawn **codebase-pattern-finder** or **codebase-analyzer** agents to examine specific patterns or approaches.

3. **Present open questions and wait for answers.** Before writing anything, you MUST:
   - List 3-5 design questions that require human judgment
   - Present options with trade-offs for each, grounded in what the research found
   - Wait for the user to respond

   Example:
   ```
   Before I write the design document, I need your input:

   **Q1: Data model approach**
   The research shows two patterns in the codebase:
   - Option A: [pattern from research.md] — used in [file:line], simpler but less flexible
   - Option B: [pattern from research.md] — used in [file:line], more complex but extensible
   Which fits this use case?

   **Q2: ...**
   ```

   Do NOT skip this step. Do NOT write the design document without user input.

4. **Write `design.md`** (~200 lines) to the artifact directory:

   ```markdown
   # Design Discussion

   ## Current State
   [What exists today, grounded in research findings with file:line refs]

   ## Desired End State
   [What we're building and how to verify it's correct]

   ## Patterns to Follow
   [Existing codebase patterns the implementation should match, with file:line refs.
   Flag any patterns the research found that should NOT be followed.]

   ## Design Decisions
   1. **[Decision name]**: [chosen option] — [why]
   2. **[Decision name]**: [chosen option] — [why]
   ...

   ## What We're NOT Doing
   [Explicit scope boundaries to prevent creep]

   ## Open Risks
   [Anything uncertain that might surface during implementation]
   ```

5. **Present the design to the user** for review. Iterate until they approve.

## Output

- File written: `thoughts/qrspi/<id>/design.md`
- Tell the user: "Next: run `/qrspi-4-structure thoughts/qrspi/<id>/`"

## Rules

- ~200 lines max. This is a steering document, not a specification.
- Every pattern reference must cite `file:line` from the research.
- You MUST ask questions and wait before writing. No exceptions.
- "Patterns to Follow" is critical — call out both good and bad patterns found in the codebase.
- "What We're NOT Doing" prevents scope creep downstream.

## When to Go Back

If the research is missing critical information needed for design decisions — the questions missed an important area of the codebase — tell the user and suggest re-running `/qrspi-1-question` and `/qrspi-2-research` to fill the gap before proceeding with an incomplete design.

## Subagents

This phase uses `codebase-analyzer`, `codebase-pattern-finder`. Their instructions are bundled at `references/agents/<name>.md`, relative to this `SKILL.md`. This plugin installs these as custom agents. Run them as subagents by name when your session can. If they are not available, read the matching file and pass its contents to the subagent as its instructions, followed by your request. With no subagent tool, follow the instructions yourself, one investigation at a time.
