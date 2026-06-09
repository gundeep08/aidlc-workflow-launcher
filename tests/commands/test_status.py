from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.status import status


class TestStatusCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.commands.status.workspace_config_service")
    def test_no_config_fails(self, mock_config, tmp_path):
        mock_config.load_config.return_value = {}
        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(status)
            assert result.exit_code == 1

    @patch("cli.commands.status.staleness_service")
    @patch("cli.commands.status.state_service")
    @patch("cli.commands.status.workspace_config_service")
    def test_displays_repo_table(self, mock_config, mock_state, mock_stale, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_config.get_code_repos.return_value = [{"name": "eviv-api-v3", "path": "code/eviv-api-v3"}]
        mock_stale.check_staleness.return_value = {"reason": "fresh", "stale": False, "commits_since": 0}
        mock_state.find_state_file.return_value = None

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(status)
            assert result.exit_code == 0
            assert "eviv-api-v3" in result.output

    @patch("cli.commands.status.workspace_config_service")
    def test_no_repos_message(self, mock_config, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_config.get_code_repos.return_value = []
        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(status)
            assert "No repos registered" in result.output
