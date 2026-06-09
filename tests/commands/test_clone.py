from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.clone import clone


class TestCloneCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.commands.clone.workspace_config_service")
    def test_no_config_fails(self, mock_config, tmp_path):
        mock_config.load_config.return_value = {}
        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(clone, ["git@host:repo.git"])
            assert result.exit_code == 1

    @patch("cli.commands.clone.workspace_config_service")
    @patch("cli.commands.clone.git_service")
    def test_clones_new_repo(self, mock_git, mock_config, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_config.derive_repo_name.return_value = "my-repo"
        mock_config.add_code_repo.return_value = {"platform": "amazon-q", "repos": []}

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(clone, ["git@host:my-repo.git"])
            assert result.exit_code == 0
            assert "Cloned my-repo" in result.output

    @patch("cli.commands.clone.workspace_config_service")
    @patch("cli.commands.clone.git_service")
    def test_skips_existing_repo(self, mock_git, mock_config, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_config.derive_repo_name.return_value = "my-repo"
        mock_config.add_code_repo.return_value = {"platform": "amazon-q", "repos": []}

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / "code" / "my-repo").mkdir(parents=True)
            result = self.runner.invoke(clone, ["git@host:my-repo.git"])
            assert "already exists" in result.output
            mock_git.clone_repo.assert_not_called()
