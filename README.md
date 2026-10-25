# public-marketplace

One plugin marketplace that ships two coding-agent workflows to **Claude Code**, **OpenAI Codex**, and **GitHub Copilot** (CLI and VS Code).

| Plugin | What it is | Upstream |
| --- | --- | --- |
| `rpi` | Research, design, implement. One skill that walks a change through research questions, research, a design step (design discussion, PRD then TDD, or TDD), an optional outline, and implementation, saving each step as a local document. | [humanlayer/skills](https://github.com/humanlayer/skills/tree/main/plugins/rpi) (HumanLayer) |
| `qrspi` | Question, Research, Design, Structure, Plan, Worktree, Implement, PR. Eight phases, each in its own context, with a markdown artifact between them. | [matanshavit/qrspi](https://github.com/matanshavit/qrspi) (Matan Shavit) |

The exact upstream commits are pinned in [`upstream.json`](upstream.json).

## Install

### Claude Code

```bash
claude plugin marketplace add rachel-switzer-nerdery/public-marketplace
claude plugin install rpi@public-marketplace
claude plugin install qrspi@public-marketplace
```

Or inside a session: `/plugin marketplace add rachel-switzer-nerdery/public-marketplace`, then `/plugin install rpi@public-marketplace`.

### Codex

```bash
codex plugin marketplace add rachel-switzer-nerdery/public-marketplace
codex plugin add rpi@public-marketplace
codex plugin add qrspi@public-marketplace
```

You can also install from `/plugins` in the Codex CLI or app. Start a new session after installing.

### GitHub Copilot CLI

```bash
copilot plugin marketplace add rachel-switzer-nerdery/public-marketplace
copilot plugin install rpi@public-marketplace
copilot plugin install qrspi@public-marketplace
```

### VS Code (Copilot agent plugins)

Add the marketplace to your user `settings.json`:

```json
"chat.plugins.marketplaces": ["rachel-switzer-nerdery/public-marketplace"]
```

Then search `@agentPlugins` in the Extensions view, or run **Chat: Install Plugin From Source**.

## Use

| | Claude Code | Codex | Copilot |
| --- | --- | --- | --- |
| RPI | `/rpi <task or step>` | `$rpi <task or step>` | `/rpi <task or step>` |
| QRSPI phase 1 | `/qrspi:1_question <task>` | `$qrspi-1-question <task>` | `/qrspi-1-question <task>` |
| QRSPI phases 2–8 | `/qrspi:2_research thoughts/qrspi/<id>/` … | `$qrspi-2-research thoughts/qrspi/<id>/` … | `/qrspi-2-research thoughts/qrspi/<id>/` … |

Each phase tells you the next command to run. Run every phase in a fresh session.

- **RPI** writes to `.agents/artifacts/<task>/`. Codex's default sandbox can make `.agents` read-only. If it does, give the session write access to `.agents/artifacts` or pass another directory. See the [upstream README](https://github.com/humanlayer/skills#rpi) for the full flow.
- **QRSPI** writes to `thoughts/qrspi/<id>/`. See the [upstream README](https://github.com/matanshavit/qrspi#usage) for when to skip phases.

Both workflows use the same artifact formats on every harness, so you can start a task in one tool and finish it in another.

## How each harness gets the workflows

| | Claude Code | Codex | Copilot |
| --- | --- | --- | --- |
| Marketplace manifest | `.claude-plugin/marketplace.json` | `.agents/plugins/marketplace.json` | `.github/plugin/marketplace.json` |
| Plugin manifest | `claude/<p>/.claude-plugin/plugin.json` | `codex/<p>/.codex-plugin/plugin.json` | `copilot/<p>/plugin.json` |
| RPI | Upstream plugin unchanged: skill + 5 agents | Skill only | Skill + 5 `.agent.md` agents |
| QRSPI | 8 commands + 4 agents | 8 skills | 8 skills + 4 `.agent.md` agents |

Notes on the conversions:

- **Codex plugins carry no subagents.** The RPI skill already handles this: it reads the agent instructions bundled under `references/subagents/` and passes them to whatever subagent tool the session has. The QRSPI skills do the same with `references/agents/`.
- **QRSPI commands became skills on Codex and Copilot**, because those harnesses load skills from plugins but have no plugin slash commands that work the same way on both. Each skill is the upstream command with three changes:
  - `$ARGUMENTS` becomes an explicit `<dir>` input.
  - The next-step hints use that harness's invocation syntax.
  - A Subagents section points at the bundled agent instructions.
- **Copilot agents** keep the upstream agent body. Their frontmatter maps Claude tool names to Copilot aliases (`read`, `search`, `edit`, `execute`, `web`, `todo`) and drops the Claude-only `model` and `color` keys.
- **Agent name overlap on Copilot.** Both plugins ship agents named `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, and `web-search-researcher`, and Copilot does not namespace plugin agents. If you install both plugins, one copy of each name wins. The two copies differ only slightly (RPI's versions may run shell commands).

## Update from upstream

Everything under `claude/`, `codex/`, `copilot/` and the three marketplace manifests is generated. Don't edit those files by hand.

1. Set the new commit SHAs in `upstream.json`.
2. Rebuild:

   ```bash
   python3 scripts/build.py
   ```

3. Check the result:

   ```bash
   claude plugin validate .
   ```

4. Bump the plugin `version` in `scripts/build.py` when the content changes, so installed copies update.

`scripts/build.py --src DIR` builds from existing local clones instead (`DIR/rpi` = humanlayer/skills, `DIR/qrspi` = matanshavit/qrspi).

## License

The workflow content is MIT-licensed by its authors: © 2026 HumanLayer (`rpi`) and © 2026 Matan Shavit (`qrspi`). Each plugin directory carries its upstream `LICENSE`. The build script and manifests in this repo are MIT as well; see [LICENSE](LICENSE).
