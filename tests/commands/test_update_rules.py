from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from cli.commands.update_rules import update_rules


class TestUpdateRulesCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.commands.update_rules.workspace_config_service")
    def test_no_config_fails(self, mock_config, tmp_path):
        mock_config.load_config.return_value = {}
        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(update_rules)
            assert result.exit_code == 1

    @patch("cli.commands.update_rules.workspace_config_service")
    @patch("cli.commands.update_rules.platform_service")
    @patch("cli.commands.update_rules.github_release_service")
    def test_updates_rules(self, mock_github, mock_platform, mock_config, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q", "rules_version": "v0.1.7"}
        mock_config.get_platform.return_value = "amazon-q"
        mock_github.get_latest_release_info.return_value = {"tag": "v0.1.8", "download_url": "http://x"}
        mock_github.download_release_zip.return_value = tmp_path / "release.zip"
        mock_github.extract_rules.return_value = tmp_path / "extracted"

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(update_rules)
            assert result.exit_code == 0
            assert "v0.1.7" in result.output
            assert "v0.1.8" in result.output
