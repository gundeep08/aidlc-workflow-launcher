from pathlib import Path

import click

from cli.config.constants import CODE_DIR, DOCS_DIR, AIDLC_DOCS_SUBDIR, RE_SKILLS_SUBDIR, AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import git_service, workspace_config_service, state_service, staleness_service, github_release_service, platform_service


@click.command()
def start():
    """Start or resume an AI-DLC workflow."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        docs_url = workspace_config_service.get_docs_repo_url(config)
        if not docs_url:
            raise ConfigNotFoundError("No docs repo configured. Run 'aidlc init' first.")

        docs_repo_name = workspace_config_service.derive_repo_name(docs_url)
        docs_repo_dir = workspace_root / DOCS_DIR / docs_repo_name
        aidlc_docs_base = docs_repo_dir / AIDLC_DOCS_SUBDIR
        re_skills_base = docs_repo_dir / RE_SKILLS_SUBDIR

        # --- Step 1: Code repo selection ---
        repo_name = _select_code_repo(workspace_root, config)
        config = workspace_config_service.load_config(workspace_root)

        # --- Step 2: Docs module selection ---
        module_name = _select_docs_module(aidlc_docs_base, repo_name)

        project_dir = aidlc_docs_base / module_name

        # --- Health check ---
        lines, has_warnings, no_re = _collect_health_status(config, workspace_root, docs_repo_dir, re_skills_base, repo_name)
        click.echo("")
        for line in lines:
            click.echo(f"  {line}")
        if has_warnings:
            if not click.confirm("\nContinue anyway?", default=True):
                raise SystemExit(0)

        # --- Step 3: Feature selection ---
        existing = _find_existing_workflows(project_dir)

        if existing:
            click.echo(f"\n📋 Existing features for {module_name}:\n")
            for i, (name, stage) in enumerate(existing, 1):
                click.echo(f"    {i}) {name} ({stage})")
            click.echo(f"    N) Start new feature")
            choice = click.prompt("\nSelect feature to resume or N for new", default="1").strip()

            if choice.upper() == "N":
                feature_name = click.prompt("Feature name")
            else:
                idx = int(choice) - 1
                feature_name = existing[idx][0]
        else:
            feature_name = click.prompt("Feature name")

        # Create feature directory
        workflow_dir = project_dir / feature_name
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # --- Step 4: Branch creation ---
        branch_name = f"feature/{feature_name}"
        branch_name = click.prompt("Branch name", default=branch_name)

        code_repo_dir = workspace_root / CODE_DIR / repo_name
        if code_repo_dir.exists():
            git_service.checkout_branch(code_repo_dir, branch_name)
            click.echo(f"✓ Branch '{branch_name}' in code/{repo_name}")
        else:
            click.echo(f"⚠ Code repo not found at code/{repo_name} — skipping branch creation")

        if docs_repo_dir.exists():
            git_service.checkout_branch(docs_repo_dir, branch_name)
            click.echo(f"✓ Branch '{branch_name}' in docs/{docs_repo_name}")
        else:
            click.echo(f"⚠ Docs repo not found at docs/{docs_repo_name} — skipping branch creation")

        # Create/update symlink
        aidlc_docs_link = workspace_root / "aidlc-docs"
        if aidlc_docs_link.is_symlink() or aidlc_docs_link.exists():
            aidlc_docs_link.unlink()
        aidlc_docs_link.symlink_to(workflow_dir)

        relative_path = workflow_dir.relative_to(workspace_root)
        click.echo(f"\n✓ Symlink: aidlc-docs/ → {relative_path}/")

        # Resolve and write context-specific prompts with actual repo values
        platform = workspace_config_service.get_platform(config)
        if platform:
            docs_prompts_dir = docs_repo_dir / "prompts"
            platform_service.write_resolved_prompts(
                platform, docs_prompts_dir, workspace_root,
                {"repo_name": repo_name, "docs_repo_name": docs_repo_name}
            )

        # End of flow
        re_skills_repo_dir = re_skills_base / repo_name
        docs_re_path = f"docs/{docs_repo_name}/skills/{repo_name}/"
        staleness = staleness_service.check_staleness(repo_name, re_skills_base, workspace_root / CODE_DIR / repo_name)

        if staleness["reason"] == "no_re":
            re_skills_repo_dir.mkdir(parents=True, exist_ok=True)
            prompt_cmd = platform_service.get_prompt_command(platform, "re-create") if platform else None
            click.echo(f"\n  No RE skills found. Open your AI chat and either:")
            click.echo("")
            if prompt_cmd:
                click.echo(f"  Option A — Use the registered prompt: {prompt_cmd}")
                click.echo("")
                click.echo(f"  Option B — Paste this prompt manually:")
            else:
                click.echo(f"  Paste the following prompt:")
            click.echo("")
            click.echo("┌──────────────────────────────────────────────────────────────┐")
            click.echo(f"│  Using AI-DLC, reverse engineer the codebase at              │")
            click.echo(f"│  code/{repo_name + '/':<54}│")
            click.echo(f"│  Keep the output concise — this is for AI agent orientation  │")
            click.echo(f"│  only, not full documentation. Each file must be under 100   │")
            click.echo(f"│  lines. Store the output in {docs_re_path:<34}│")
            click.echo("└──────────────────────────────────────────────────────────────┘")
        elif staleness["stale"]:
            prompt_cmd = platform_service.get_prompt_command(platform, "re-update") if platform else None
            click.echo(f"\n  RE skills are stale ({staleness['commits_since']} commits behind). Open your AI chat and either:")
            click.echo("")
            if prompt_cmd:
                click.echo(f"  Option A — Use the registered prompt: {prompt_cmd}")
                click.echo("")
                click.echo(f"  Option B — Paste this prompt manually:")
            else:
                click.echo(f"  Paste the following prompt:")
            click.echo("")
            click.echo("┌──────────────────────────────────────────────────────────────┐")
            click.echo(f"│  Using AI-DLC, update RE skills for                          │")
            click.echo(f"│  code/{repo_name + '/':<54}│")
            click.echo(f"│  Review and update existing skills in {docs_re_path:<23}│")
            click.echo("└──────────────────────────────────────────────────────────────┘")
        else:
            load_cmd = platform_service.get_prompt_command(platform, "re-load") if platform else None
            if load_cmd:
                click.echo(f"\n✅ Ready — open your AI chat, use {load_cmd} to load RE skills, then describe what you want to build.")
            else:
                click.echo("\n✅ Ready — open your AI chat and describe what you want to build.")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)


def _select_code_repo(workspace_root: Path, config: dict) -> str:
    """Step 1: Select existing code repo or clone a new one."""
    code_dir = workspace_root / CODE_DIR
    existing = []
    if code_dir.exists():
        existing = sorted(
            d.name for d in code_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    if existing:
        click.echo("\n📦 Code repos:\n")
        for i, name in enumerate(existing, 1):
            click.echo(f"    {i}) {name}")
        click.echo(f"    N) Clone a new repo")
        choice = click.prompt("\nSelect code repo", default="1").strip()

        if choice.upper() != "N":
            return existing[int(choice) - 1]

    # Clone new repo
    repo_url = click.prompt("Code repo git URL")
    repo_name = workspace_config_service.derive_repo_name(repo_url)
    code_dir.mkdir(exist_ok=True)
    code_target = code_dir / repo_name
    if not code_target.exists():
        click.echo(f"Cloning {repo_name}...")
        git_service.clone_repo(repo_url, code_target)
        click.echo(f"✓ Cloned {repo_name}")
    repo_path = f"{CODE_DIR}/{repo_name}"
    config = workspace_config_service.add_code_repo(config, repo_name, repo_url, repo_path)
    workspace_config_service.save_config(workspace_root, config)
    return repo_name


def _select_docs_module(aidlc_docs_base: Path, default_name: str) -> str:
    """Step 2: Select existing docs module or create a new one."""
    existing = _find_existing_projects(aidlc_docs_base)

    if existing:
        click.echo("\n📋 Docs modules:\n")
        for i, name in enumerate(existing, 1):
            click.echo(f"    {i}) {name}")
        click.echo(f"    N) Create new module")
        choice = click.prompt("\nSelect docs module", default="1").strip()

        if choice.upper() != "N":
            return existing[int(choice) - 1]

    return click.prompt("Docs module name", default=default_name)


def _collect_health_status(config: dict, workspace_root: Path, docs_repo_dir: Path, re_skills_base: Path, repo_name: str) -> tuple[list[str], bool, bool]:
    """Return status lines, has_warnings flag, and no_re flag."""
    lines = []
    has_warnings = False
    no_re = False

    # Rules version
    local_version = config.get("rules_version")
    if not local_version:
        lines.append("⚠ AI-DLC rules not installed — run 'aidlc update-rules'")
        has_warnings = True
    else:
        try:
            latest = github_release_service.get_latest_release_info(
                AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
            )
            if latest["tag"] != local_version:
                lines.append(f"⚠ AI-DLC rules outdated ({local_version} → {latest['tag']}) — run 'aidlc update-rules'")
                has_warnings = True
            else:
                lines.append(f"✓ AI-DLC rules up to date ({local_version})")
        except Exception:
            lines.append(f"✓ AI-DLC rules {local_version} (could not check remote)")

    # Docs repo staleness
    if docs_repo_dir.exists():
        behind = git_service.commits_behind_remote(docs_repo_dir)
        if behind and behind > 0:
            lines.append(f"⚠ Docs repo is {behind} commit(s) behind remote — run 'aidlc update-docs'")
            has_warnings = True
        else:
            lines.append("✓ Docs repo up to date")

    # RE skills staleness
    code_repo_dir = workspace_root / CODE_DIR / repo_name
    staleness = staleness_service.check_staleness(repo_name, re_skills_base, code_repo_dir)
    if staleness["reason"] == "no_re":
        lines.append(f"⚠ No RE skills found for {repo_name}")
        no_re = True
    elif staleness["stale"]:
        lines.append(f"⚠ RE skills for {repo_name} are stale ({staleness['commits_since']} commits) — run 'aidlc re {repo_name}'")
        has_warnings = True
    else:
        lines.append(f"✓ RE skills up to date ({repo_name})")

    return lines, has_warnings, no_re


def _find_existing_projects(aidlc_docs_base: Path) -> list[str]:
    """Find existing module subdirectories under docs/ in the docs repo."""
    if not aidlc_docs_base.exists():
        return []
    return [
        d.name for d in sorted(aidlc_docs_base.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]


def _find_existing_workflows(project_dir: Path) -> list[tuple[str, str]]:
    """Find existing workflow directories and their current stage."""
    if not project_dir.exists():
        return []
    workflows = []
    for subdir in sorted(project_dir.iterdir()):
        if not subdir.is_dir():
            continue
        state_file = subdir / "aidlc-state.md"
        if state_file.exists():
            state = state_service.parse_state(state_file)
            stage = state_service.get_current_stage(state)
        else:
            stage = "Not started"
        workflows.append((subdir.name, stage))
    return workflows
