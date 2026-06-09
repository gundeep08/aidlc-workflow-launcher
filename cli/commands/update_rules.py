import tempfile
from pathlib import Path

import click

from cli.config.constants import AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
from cli.exceptions import AidlcError, ConfigNotFoundError, PlatformNotConfiguredError
from cli.services import github_release_service, platform_service, workspace_config_service


@click.command("update-rules")
def update_rules():
    """Download latest aidlc-workflows release and update rules."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        # Determine platform
        platform = workspace_config_service.get_platform(config)
        if not platform:
            platform = platform_service.detect_current_platform(workspace_root)
        if not platform:
            raise PlatformNotConfiguredError("No platform configured. Run 'aidlc init' first.")

        old_version = config.get("rules_version", "unknown")

        click.echo("Fetching latest AI-DLC rules...")
        release = github_release_service.get_latest_release_info(
            AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zip_path = tmp_path / "release.zip"
            github_release_service.download_release_zip(release["download_url"], zip_path)
            extracted = github_release_service.extract_rules(zip_path, tmp_path / "extracted")
            platform_service.place_rules(platform, extracted, workspace_root)

        config["rules_version"] = release["tag"]
        workspace_config_service.save_config(workspace_root, config)
        click.echo(f"✅ Rules updated: {old_version} → {release['tag']}")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)
