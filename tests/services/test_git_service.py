import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli.services import git_service
from cli.exceptions import GitNotInstalledError, GitCloneError


class TestIsGitInstalled:
    @patch("subprocess.run")
    def test_returns_true_when_git_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert git_service.is_git_installed() is True

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_git_missing(self, mock_run):
        assert git_service.is_git_installed() is False


class TestCloneRepo:
    @patch("cli.services.git_service.is_git_installed", return_value=False)
    def test_raises_when_git_not_installed(self, mock_git):
        with pytest.raises(GitNotInstalledError):
            git_service.clone_repo("git@host:repo.git", Path("/tmp/target"))

    @patch("cli.services.git_service.is_git_installed", return_value=True)
    @patch("subprocess.run")
    def test_raises_on_clone_failure(self, mock_run, mock_git):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: not found")
        with pytest.raises(GitCloneError, match="not found"):
            git_service.clone_repo("git@host:repo.git", Path("/tmp/target"))

    @patch("cli.services.git_service.is_git_installed", return_value=True)
    @patch("subprocess.run")
    def test_success(self, mock_run, mock_git):
        mock_run.return_value = MagicMock(returncode=0)
        git_service.clone_repo("git@host:repo.git", Path("/tmp/target"))
        mock_run.assert_called_once()


class TestGetCommitCountSince:
    @patch("subprocess.run")
    def test_returns_count(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="5\n")
        assert git_service.get_commit_count_since(Path("/repo"), "2025-01-01") == 5


class TestGetLatestCommitDate:
    @patch("subprocess.run")
    def test_returns_iso_date(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="2025-01-30T14:00:00+00:00\n")
        assert git_service.get_latest_commit_date(Path("/repo")) == "2025-01-30T14:00:00+00:00"
