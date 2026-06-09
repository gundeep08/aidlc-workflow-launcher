# aidlc-cli — AI-DLC Workflow Launcher

CLI tool for setting up and managing AI-DLC workspaces with multi-repo separation.

## Prerequisites

- Python 3.11+
- git on PATH
- Access to your team's Bitbucket/GitHub repos

## Installation

```bash
git clone <this-repo-url>
cd aidlc-workflow-launcher
pip3 install -e ".[dev]"
```

---

## First-Time Setup (Required — once per machine)

```bash
aidlc init
```

This will:
1. Ask which AI coding assistant you use (Amazon Q, Kiro, Cursor, Cline, Claude Code, GitHub Copilot)
2. Download the latest AI-DLC workflow rules from GitHub
3. Place rules in the correct platform-specific location
4. Ask for your team's docs repo git URL
5. Clone the docs repo into `docs/<docs-repo-name>/`

> **Idempotent** — safe to re-run. Skips anything already configured.

---

## Daily Workflow (Every new feature)

### Start a new feature

```bash
aidlc start
```

This will:
1. Show available code repos (or prompt to clone a new one)
2. Show existing docs modules (or create a new one)
3. Show existing features for that module (or start a new one)
4. Ask for a branch name (defaults to `feature/<feature-name>`)
5. Create the branch in both code and docs repos
6. Set up the `aidlc-docs/` symlink pointing to the feature's docs folder
7. Guide you to run Reverse Engineering if RE skills are missing

After `aidlc start`, open your AI chat and describe what you want to build.

---

## Returning Developer

If you've already done the first-time setup and are coming back to continue work:

```bash
aidlc start
```

Select your existing code repo and feature when prompted — this will switch branches and restore the symlink for your in-progress feature.

To check the status of all your projects:

```bash
aidlc status
```

---

## Commands Reference

| Command | When to use | Description |
|---|---|---|
| `aidlc init` | First-time setup | Initialize workspace: select platform, download rules, clone docs repo |
| `aidlc start` | Every new feature | Select code repo, docs module, create feature branches, set up symlink |
| `aidlc status` | Anytime | Show project states, RE staleness, and rules version |
| `aidlc re [repo-name]` | When RE skills are stale | Pull latest code and show RE prompt |
| `aidlc update-rules` | When rules are outdated | Download latest AI-DLC rules from GitHub |
| `aidlc update-docs` | When docs repo is behind | Pull latest changes for the docs repo |
| `aidlc clone <repo-urls...>` | Optional | Clone one or more code repos without starting a workflow |

---

## Workspace Structure

After setup, your workspace looks like:

```
aidlc-workflow-launcher/          ← you are here
├── workspace-config.yml          ← CLI state (platform, repos)
├── .amazonq/ or .kiro/ or .github/ ← git-ignored, AI-DLC rules (platform-specific)
├── aidlc-docs/                   ← git-ignored, symlink → docs/<docs-repo>/aidlc-docs/<module>/<feature>/
├── code/                         ← git-ignored, cloned by CLI
│   └── <repo-name>/
└── docs/                         ← git-ignored, cloned by CLI
    └── <docs-repo-name>/
        ├── aidlc-docs/
        │   └── <repo-name>/
        │       └── <feature-name>/   ← feature workflow docs
        │           ├── aidlc-state.md
        │           ├── audit.md
        │           ├── inception/
        │           └── construction/
        └── re-skills/
            └── <repo-name>/
                ├── 01-business-overview.md
                └── ...
```

## Supported Platforms

- Amazon Q Developer
- Kiro
- Cursor
- Cline
- Claude Code
- GitHub Copilot

## Running Tests

```bash
pip3 install -e ".[dev]"
pytest tests/ -v
```
