from pathlib import Path

import click

from cli.config.constants import CODE_DIR, DOCS_DIR, AIDLC_DOCS_SUBDIR, RE_SKILLS_SUBDIR
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import git_service, workspace_config_service, state_service, staleness_service


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

        # Check RE skills and guide user
        re_skills_repo_dir = re_skills_base / repo_name
        if not staleness_service.has_re_skills(re_skills_base, repo_name):
            re_skills_repo_dir.mkdir(parents=True, exist_ok=True)
            docs_re_path = f"docs/{docs_repo_name}/re-skills/{repo_name}/"
            click.echo(f"\n⚠  No Reverse Engineering skills found for '{repo_name}'")
            click.echo("  Open your AI chat and paste the following prompt:")
            click.echo("")
            click.echo("┌──────────────────────────────────────────────────────────────┐")
            click.echo(f"│  Using AI-DLC, reverse engineer the codebase at              │")
            click.echo(f"│  code/{repo_name + '/':<54}│")
            click.echo(f"│  and generate the skills/knowledge base files.               │")
            click.echo(f"│  Store the output in {docs_re_path:<41}│")
            click.echo("└──────────────────────────────────────────────────────────────┘")
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


def _find_existing_projects(aidlc_docs_base: Path) -> list[str]:
    """Find existing module subdirectories under aidlc-docs/ in the docs repo."""
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
