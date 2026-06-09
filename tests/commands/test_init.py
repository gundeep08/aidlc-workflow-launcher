from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.init import init


class TestInitCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.commands.init.workspace_config_service")
    @patch("cli.commands.init.platform_service")
    @patch("cli.commands.init.github_release_service")
    def test_fresh_init(self, mock_github, mock_platform, mock_config, tmp_path):
        mock_config.load_config.return_value = {}
        mock_config.get_platform.return_value = None
        mock_config.get_docs_repo_url.return_value = None
        mock_platform.get_display_names.return_value = [("amazon-q", "Amazon Q Developer")]
        mock_platform.get_rules_path.return_value = ".amazonq/rules/aws-aidlc-rules/"
        mock_github.get_latest_release_info.return_value = {"tag": "v0.1.8", "download_url": "http://x"}
        mock_github.download_release_zip.return_value = tmp_path / "release.zip"
        mock_github.extract_rules.return_value = tmp_path / "extracted"

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(init, input="1\ngit@host:docs.git\n")
            assert result.exit_code == 0
            assert "initialized successfully" in result.output

    @patch("cli.commands.init.workspace_config_service")
    @patch("cli.commands.init.platform_service")
    def test_idempotent_skips_configured(self, mock_platform, mock_config, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q", "docs_repo_url": "git@host:docs.git"}
        mock_config.get_platform.return_value = "amazon-q"
        mock_config.get_docs_repo_url.return_value = "git@host:docs.git"
        mock_platform.get_rules_path.return_value = ".amazonq/rules/aws-aidlc-rules/"

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            # Create rules dir to simulate already present
            (Path.cwd() / ".amazonq/rules/aws-aidlc-rules").mkdir(parents=True)
            result = self.runner.invoke(init)
            assert result.exit_code == 0
            assert "already done" in result.output
