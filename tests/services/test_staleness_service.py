from pathlib import Path
from unittest.mock import patch

from cli.services import staleness_service


class TestGetReTimestamp:
    def test_returns_timestamp_from_metadata(self, tmp_path):
        repo_dir = tmp_path / "eviv-api-v3"
        repo_dir.mkdir()
        (repo_dir / "metadata.yml").write_text("last_updated: 2025-01-15T10:00:00Z\n")
        result = staleness_service.get_re_timestamp(tmp_path, "eviv-api-v3")
        assert "2025-01-15" in result
        assert "10:00:00" in result

    def test_returns_none_when_no_metadata(self, tmp_path):
        assert staleness_service.get_re_timestamp(tmp_path, "nonexistent") is None


class TestCheckStaleness:
    @patch("cli.services.git_service.get_commit_count_since", return_value=3)
    def test_stale_when_commits_exist(self, mock_git, tmp_path):
        re_dir = tmp_path / "re"
        repo_re = re_dir / "my-repo"
        repo_re.mkdir(parents=True)
        (repo_re / "metadata.yml").write_text("last_updated: 2025-01-01T00:00:00Z\n")
        result = staleness_service.check_staleness("my-repo", re_dir, tmp_path / "code/my-repo")
        assert result["stale"] is True
        assert result["commits_since"] == 3
        assert result["reason"] == "stale"

    @patch("cli.services.git_service.get_commit_count_since", return_value=0)
    def test_fresh_when_no_commits(self, mock_git, tmp_path):
        re_dir = tmp_path / "re"
        repo_re = re_dir / "my-repo"
        repo_re.mkdir(parents=True)
        (repo_re / "metadata.yml").write_text("last_updated: 2025-01-30T00:00:00Z\n")
        result = staleness_service.check_staleness("my-repo", re_dir, tmp_path / "code/my-repo")
        assert result["stale"] is False
        assert result["reason"] == "fresh"

    def test_no_re_metadata(self, tmp_path):
        result = staleness_service.check_staleness("my-repo", tmp_path, tmp_path / "code/my-repo")
        assert result["stale"] is True
        assert result["reason"] == "no_re"


class TestGetAllStaleness:
    @patch("cli.services.git_service.get_commit_count_since", return_value=1)
    def test_checks_all_repos_with_re(self, mock_git, tmp_path):
        re_dir = tmp_path / "re"
        code_dir = tmp_path / "code"
        for name in ["repo-a", "repo-b"]:
            (re_dir / name).mkdir(parents=True)
            (re_dir / name / "metadata.yml").write_text("last_updated: 2025-01-01T00:00:00Z\n")
            (code_dir / name).mkdir(parents=True)
        results = staleness_service.get_all_staleness(re_dir, code_dir)
        assert len(results) == 2
