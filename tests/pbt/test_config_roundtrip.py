import tempfile
from pathlib import Path

from hypothesis import given, strategies as st

from cli.services import workspace_config_service


repo_names = st.from_regex(r"[a-z][a-z0-9\-]{1,20}", fullmatch=True)
repo_entries = st.fixed_dictionaries({
    "name": repo_names,
    "url": st.from_regex(r"git@[a-z]+\.[a-z]+:[a-z]+/[a-z][a-z0-9\-]{1,20}\.git", fullmatch=True),
    "path": repo_names.map(lambda n: f"code/{n}"),
})

configs = st.fixed_dictionaries({
    "platform": st.sampled_from(["amazon-q", "kiro", "cursor", "cline", "claude-code", "github-copilot"]),
    "docs_repo_url": st.from_regex(r"git@[a-z]+\.[a-z]+:[a-z]+/[a-z\-]+\.git", fullmatch=True),
    "rules_version": st.from_regex(r"v[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True),
    "repos": st.lists(repo_entries, max_size=5),
})


class TestConfigRoundTripPBT:
    @given(config=configs)
    def test_save_load_preserves_data(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workspace_config_service.save_config(tmp_path, config)
            loaded = workspace_config_service.load_config(tmp_path)
            assert loaded["platform"] == config["platform"]
            assert loaded["docs_repo_url"] == config["docs_repo_url"]
            assert loaded["rules_version"] == config["rules_version"]
            assert len(loaded.get("repos", [])) == len(config["repos"])

    @given(config=configs)
    def test_get_platform_matches_saved(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workspace_config_service.save_config(tmp_path, config)
            loaded = workspace_config_service.load_config(tmp_path)
            assert workspace_config_service.get_platform(loaded) == config["platform"]

    @given(config=configs)
    def test_get_docs_repo_url_matches_saved(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workspace_config_service.save_config(tmp_path, config)
            loaded = workspace_config_service.load_config(tmp_path)
            assert workspace_config_service.get_docs_repo_url(loaded) == config["docs_repo_url"]
