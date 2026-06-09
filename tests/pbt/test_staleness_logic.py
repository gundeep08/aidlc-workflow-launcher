import tempfile
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, strategies as st

from cli.services import staleness_service


commit_counts = st.integers(min_value=0, max_value=10000)


class TestStalenessLogicPBT:
    @given(commits=commit_counts)
    def test_stale_iff_commits_greater_than_zero(self, commits):
        """BR-2.1: RE is stale if code repo has ≥1 commit after last_updated."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            re_dir = tmp_path / "re"
            repo_re = re_dir / "test-repo"
            repo_re.mkdir(parents=True)
            (repo_re / "metadata.yml").write_text("last_updated: 2025-01-01T00:00:00Z\n")

            with patch("cli.services.git_service.get_commit_count_since", return_value=commits):
                result = staleness_service.check_staleness("test-repo", re_dir, tmp_path / "code/test-repo")
                if commits > 0:
                    assert result["stale"] is True
                    assert result["reason"] == "stale"
                else:
                    assert result["stale"] is False
                    assert result["reason"] == "fresh"
                assert result["commits_since"] == commits

    @given(commits=commit_counts)
    def test_no_re_always_stale(self, commits):
        """BR-2.2: RE with no metadata.yml is always considered stale."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = staleness_service.check_staleness("nonexistent", tmp_path, tmp_path / "code/x")
            assert result["stale"] is True
            assert result["reason"] == "no_re"
