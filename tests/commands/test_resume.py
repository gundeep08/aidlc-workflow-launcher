from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.resume import resume


class TestResumeCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.commands.resume.workspace_config_service")
    def test_no_config_fails(self, mock_config, tmp_path):
        mock_config.load_config.return_value = {}
        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            result = self.runner.invoke(resume, ["my-project"])
            assert result.exit_code == 1

    @patch("cli.commands.resume.state_service")
    @patch("cli.commands.resume.workspace_config_service")
    def test_no_state_file_fails(self, mock_config, mock_state, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_state.find_state_file.return_value = None

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / "docs" / "my-docs").mkdir(parents=True)
            result = self.runner.invoke(resume, ["my-project"])
            assert result.exit_code == 1
            assert "No workflow found" in result.output

    @patch("cli.commands.resume.state_service")
    @patch("cli.commands.resume.workspace_config_service")
    def test_displays_resume_guidance(self, mock_config, mock_state, tmp_path):
        mock_config.load_config.return_value = {"platform": "amazon-q"}
        mock_state.find_state_file.return_value = Path("/fake/state.md")
        mock_state.parse_state.return_value = {
            "project_type": "Brownfield",
            "current_stage": "Code Generation",
            "stages": [{"name": "Code Gen", "status": "in_progress"}],
        }
        mock_state.is_workflow_in_progress.return_value = True
        mock_state.get_current_stage.return_value = "Code Generation"
        mock_state.get_completed_stages.return_value = ["Requirements"]

        with self.runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / "docs" / "my-docs").mkdir(parents=True)
            result = self.runner.invoke(resume, ["my-project"])
            assert result.exit_code == 0
            assert "Code Generation" in result.output
            assert "Resume AI-DLC workflow" in result.output
