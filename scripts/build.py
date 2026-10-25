#!/usr/bin/env python3
"""Regenerate every plugin in this marketplace from the upstream commits pinned in upstream.json.

Usage:
    python3 scripts/build.py                 # clone the pinned refs and rebuild
    python3 scripts/build.py --src DIR       # build from existing clones: DIR/rpi and DIR/qrspi

Outputs (all overwritten):
    claude/{rpi,qrspi}    Claude Code plugins
    codex/{rpi,qrspi}     Codex plugins
    copilot/{rpi,qrspi}   GitHub Copilot plugins (CLI and VS Code)
    .claude-plugin/marketplace.json, .agents/plugins/marketplace.json, .github/plugin/marketplace.json

Stdlib only. Never edit the generated directories by hand; change this script and rebuild.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = "public-marketplace"
OWNER = {"name": "rachel-switzer-nerdery"}
REPO_URL = "https://github.com/rachel-switzer-nerdery/public-marketplace"

RPI = {
    "name": "rpi",
    "version": "1.0.0",
    "description": "Research a change, work through its design, and implement it with reviewable local documents. From HumanLayer.",
    "keywords": ["research", "design", "implementation", "workflow", "humanlayer"],
    "author": {"name": "HumanLayer", "email": "support@humanlayer.dev", "url": "https://humanlayer.dev"},
    "upstream": "https://github.com/humanlayer/skills/tree/main/plugins/rpi",
}
QRSPI = {
    "name": "qrspi",
    "version": "1.0.0",
    "description": "Question, Research, Design, Structure, Plan, Worktree, Implement, PR: an 8-phase workflow that keeps each step in its own context with a markdown artifact between phases.",
    "keywords": ["question", "research", "design", "structure", "plan", "implement", "workflow"],
    "author": {"name": "Matan Shavit", "url": "https://github.com/matanshavit"},
    "upstream": "https://github.com/matanshavit/qrspi",
}
QRSPI_PHASES = ["1_question", "2_research", "3_design", "4_structure", "5_plan", "6_worktree", "7_implement", "8_pr"]
QRSPI_AGENTS = ["codebase-locator", "codebase-analyzer", "codebase-pattern-finder", "web-search-researcher"]

# Claude tool name -> Copilot tool alias (https://docs.github.com/en/copilot/reference/custom-agents-configuration)
COPILOT_TOOLS = {
    "Read": "read", "Grep": "search", "Glob": "search", "LS": "search",
    "Edit": "edit", "Write": "edit", "Bash": "execute",
    "WebSearch": "web", "WebFetch": "web", "TodoWrite": "todo",
}


# ---------- helpers ----------

def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def unquote(v):
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return json.loads(v)
    return v


def yaml_str(v):
    return json.dumps(v, ensure_ascii=False)


def frontmatter(pairs):
    lines = ["---"] + [f"{k}: {v}" for k, v in pairs] + ["---", ""]
    return "\n".join(lines)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path, data):
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def reset(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def fetch(src_root, upstream):
    for name, spec in upstream.items():
        dest = src_root / name
        subprocess.run(["git", "init", "-q", str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", spec["repo"], spec["ref"]], check=True)
        subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)


# ---------- RPI ----------

def build_rpi(src, upstream):
    plugin_src = src / upstream["path"]
    license_src = src / "LICENSE"

    # Claude Code: the upstream plugin as-is.
    out = ROOT / "claude/rpi"
    reset(out)
    shutil.copytree(plugin_src / "skills", out / "skills")
    shutil.copytree(plugin_src / "agents", out / "agents")
    shutil.copy(license_src, out / "LICENSE")
    manifest = json.loads((plugin_src / ".claude-plugin/plugin.json").read_text())
    manifest.update(version=RPI["version"], description=RPI["description"], author=RPI["author"],
                    homepage=RPI["upstream"], repository=REPO_URL)
    write_json(out / ".claude-plugin/plugin.json", manifest)

    # Codex: skills only. The skill reads bundled subagent instructions from
    # references/subagents/ when the named agents are not installed.
    out = ROOT / "codex/rpi"
    reset(out)
    shutil.copytree(plugin_src / "skills", out / "skills")
    shutil.copy(license_src, out / "LICENSE")
    write_json(out / ".codex-plugin/plugin.json", codex_manifest(RPI, "RPI", "Research, design, implement",
                                                                  ["$rpi research how auth sessions are stored",
                                                                   "$rpi make a PRD .agents/artifacts/my-change",
                                                                   "$rpi implement .agents/artifacts/my-change"]))

    # Copilot: the skill plus agents converted to .agent.md.
    out = ROOT / "copilot/rpi"
    reset(out)
    shutil.copytree(plugin_src / "skills", out / "skills")
    for agent in sorted((plugin_src / "agents").glob("*.md")):
        write(out / "agents" / f"{agent.stem}.agent.md", copilot_agent(agent.read_text()))
    shutil.copy(license_src, out / "LICENSE")
    write_json(out / "plugin.json", copilot_manifest(RPI))


# ---------- QRSPI ----------

def build_qrspi(src, upstream):
    claude_dir = src / upstream["path"]
    commands = {p: (claude_dir / "commands/qrspi" / f"{p}.md").read_text() for p in QRSPI_PHASES}
    agents = {a: (claude_dir / "agents" / f"{a}.md").read_text() for a in QRSPI_AGENTS}
    license_src = src / "LICENSE"

    # Claude Code: commands become /qrspi:<phase> once namespaced by the plugin.
    out = ROOT / "claude/qrspi"
    reset(out)
    for phase, text in commands.items():
        write(out / "commands" / f"{phase}.md", re.sub(r"/qrspi/(\d_\w+)", r"/qrspi:\1", text))
    for name, text in agents.items():
        write(out / "agents" / f"{name}.md", text)
    shutil.copy(license_src, out / "LICENSE")
    write_json(out / ".claude-plugin/plugin.json", {
        "name": QRSPI["name"], "version": QRSPI["version"], "description": QRSPI["description"],
        "author": QRSPI["author"], "homepage": QRSPI["upstream"], "repository": REPO_URL,
        "license": "MIT", "keywords": QRSPI["keywords"],
    })

    # Codex and Copilot have no plugin slash commands, so each phase becomes a skill.
    for harness, prefix in (("codex", "$"), ("copilot", "/")):
        out = ROOT / harness / "qrspi"
        reset(out)
        for phase, text in commands.items():
            skill = qrspi_skill(phase, text, prefix, harness)
            skill_dir = out / "skills" / skill_name(phase)
            write(skill_dir / "SKILL.md", skill)
            for name in agents_used(text):
                write(skill_dir / "references/agents" / f"{name}.md", split_frontmatter(agents[name])[1].lstrip())
        if harness == "copilot":
            for name, text in agents.items():
                write(out / "agents" / f"{name}.agent.md", copilot_agent(text))
        shutil.copy(license_src, out / "LICENSE")
        if harness == "codex":
            write_json(out / ".codex-plugin/plugin.json", codex_manifest(QRSPI, "QRSPI", "Question, research, design, plan, implement",
                                                                          ["$qrspi-1-question Add rate limiting to the API endpoints",
                                                                           "$qrspi-3-design thoughts/qrspi/<id>/",
                                                                           "$qrspi-7-implement thoughts/qrspi/<id>/"]))
        else:
            write_json(out / "plugin.json", copilot_manifest(QRSPI))


def skill_name(phase):
    return "qrspi-" + phase.replace("_", "-")


def agents_used(text):
    return [a for a in QRSPI_AGENTS if a in text]


def qrspi_skill(phase, text, prefix, harness):
    meta, body = split_frontmatter(text)
    description = unquote(meta["description"]).rstrip(".")
    hint = unquote(meta.get("argument-hint", ""))

    body = re.sub(r"/qrspi/(\d)_(\w+)", lambda m: f"{prefix}qrspi-{m.group(1)}-{m.group(2)}", body)
    body = body.replace("$ARGUMENTS", "<dir>")
    body = body.replace("Check CLAUDE.md, Makefile", "Check AGENTS.md, CLAUDE.md, Makefile")

    preface = []
    if "<dir>" in body:
        preface.append(f"`<dir>` is the artifact directory passed with this skill, for example `{hint}`. "
                       "If none was given, ask the user for it before doing anything else.")
    else:
        preface.append(f"The input is passed with this skill: {hint}. If nothing was given, ask the user for it.")
    preface.append("Start a fresh session for each phase when you can; each phase reads only its own input artifacts.")
    body = re.sub(r"^(# .+\n)", lambda m: m.group(1) + "\n" + "\n\n".join(preface) + "\n", body, count=1, flags=re.M)

    used = agents_used(text)
    if used:
        names = ", ".join(f"`{a}`" for a in used)
        if harness == "copilot":
            how = ("This plugin installs these as custom agents. Run them as subagents by name when your session can. "
                   "If they are not available, ")
        else:
            how = "If your session has a tool for running subagents, "
        body += (f"\n## Subagents\n\nThis phase uses {names}. Their instructions are bundled at "
                 f"`references/agents/<name>.md`, relative to this `SKILL.md`. {how}"
                 "read the matching file and pass its contents to the subagent as its instructions, followed by your request. "
                 "With no subagent tool, follow the instructions yourself, one investigation at a time.\n")

    return frontmatter([
        ("name", skill_name(phase)),
        ("description", yaml_str(f"QRSPI phase {phase[0]}: {description}. Only use when the user explicitly invokes this skill by name.")),
    ]) + body.lstrip("\n")


# ---------- manifests ----------

def codex_manifest(p, display, short, prompts):
    return {
        "name": p["name"], "version": p["version"], "description": p["description"],
        "author": {k: v for k, v in p["author"].items() if k != "url"},
        "homepage": p["upstream"], "repository": REPO_URL, "license": "MIT",
        "keywords": p["keywords"], "skills": "./skills/",
        "interface": {
            "displayName": display, "shortDescription": short, "longDescription": p["description"],
            "developerName": p["author"]["name"], "category": "Productivity",
            "capabilities": ["Interactive", "Read", "Write"], "websiteURL": p["upstream"],
            "defaultPrompt": prompts,
        },
    }


def copilot_manifest(p):
    manifest = {
        "name": p["name"], "version": p["version"], "description": p["description"],
        "author": {k: v for k, v in p["author"].items() if k != "url"},
        "homepage": p["upstream"], "repository": REPO_URL, "license": "MIT",
        "keywords": p["keywords"], "skills": "./skills/",
    }
    if (ROOT / "copilot" / p["name"] / "agents").exists():
        manifest["agents"] = "./agents/"
    return manifest


def copilot_agent(text):
    meta, body = split_frontmatter(text)
    tools = []
    for t in (meta.get("tools") or "").split(","):
        alias = COPILOT_TOOLS.get(t.strip())
        if alias and alias not in tools:
            tools.append(alias)
    return frontmatter([
        ("name", meta["name"]),
        ("description", yaml_str(unquote(meta["description"]))),
        ("tools", json.dumps(tools)),
    ]) + body.lstrip("\n")


def marketplaces():
    entries = [(RPI, "rpi"), (QRSPI, "qrspi")]
    write_json(ROOT / ".claude-plugin/marketplace.json", {
        "name": MARKETPLACE, "owner": OWNER,
        "metadata": {"description": "RPI and QRSPI coding-agent workflows for Claude Code.", "version": "1.0.0"},
        "plugins": [{"name": p["name"], "source": f"./claude/{d}", "description": p["description"],
                     "version": p["version"], "author": p["author"], "category": "workflow",
                     "keywords": p["keywords"]} for p, d in entries],
    })
    write_json(ROOT / ".agents/plugins/marketplace.json", {
        "name": MARKETPLACE, "interface": {"displayName": "RPI and QRSPI workflows"},
        "plugins": [{"name": p["name"], "source": {"source": "local", "path": f"./codex/{d}"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"} for p, d in entries],
    })
    write_json(ROOT / ".github/plugin/marketplace.json", {
        "name": MARKETPLACE, "owner": OWNER,
        "metadata": {"description": "RPI and QRSPI coding-agent workflows for GitHub Copilot.", "version": "1.0.0"},
        "plugins": [{"name": p["name"], "source": f"./copilot/{d}", "description": p["description"],
                     "version": p["version"], "keywords": p["keywords"]} for p, d in entries],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src", type=Path, help="directory holding existing clones named rpi/ and qrspi/")
    args = parser.parse_args()

    upstream = json.loads((ROOT / "upstream.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        src = args.src
        if src is None:
            src = Path(tmp)
            fetch(src, upstream)
        build_rpi(src / "rpi", upstream["rpi"])
        build_qrspi(src / "qrspi", upstream["qrspi"])
    marketplaces()
    print("built claude/, codex/, copilot/ and the three marketplace manifests", file=sys.stderr)


if __name__ == "__main__":
    main()
