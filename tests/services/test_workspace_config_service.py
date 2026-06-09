from pathlib import Path

from cli.services import workspace_config_service


class TestLoadConfig:
    def test_returns_empty_dict_when_no_file(self, tmp_path):
        assert workspace_config_service.load_config(tmp_path) == {}

    def test_loads_existing_config(self, tmp_path):
        config_path = tmp_path / "workspace-config.yml"
        config_path.write_text("platform: amazon-q\ndocs_repo_url: git@host:docs.git\n")
        config = workspace_config_service.load_config(tmp_path)
        assert config["platform"] == "amazon-q"
        assert config["docs_repo_url"] == "git@host:docs.git"


class TestSaveConfig:
    def test_writes_yaml(self, tmp_path):
        config = {"platform": "cursor", "repos": []}
        workspace_config_service.save_config(tmp_path, config)
        loaded = workspace_config_service.load_config(tmp_path)
        assert loaded["platform"] == "cursor"


class TestAddCodeRepo:
    def test_adds_new_repo(self):
        config = {}
        result = workspace_config_service.add_code_repo(config, "my-repo", "git@host:my-repo.git", "code/my-repo")
        assert len(result["repos"]) == 1
        assert result["repos"][0]["name"] == "my-repo"

    def test_skips_duplicate(self):
        config = {"repos": [{"name": "my-repo", "url": "git@host:my-repo.git", "path": "code/my-repo"}]}
        result = workspace_config_service.add_code_repo(config, "my-repo", "git@host:my-repo.git", "code/my-repo")
        assert len(result["repos"]) == 1


class TestDeriveRepoName:
    def test_ssh_url_with_git_suffix(self):
        assert workspace_config_service.derive_repo_name("git@bitbucket.es.ad.adp.com:projects/DSEVIV/repos/eviv-api-v3.git") == "eviv-api-v3"

    def test_https_url(self):
        assert workspace_config_service.derive_repo_name("https://github.com/org/my-repo.git") == "my-repo"

    def test_url_without_git_suffix(self):
        assert workspace_config_service.derive_repo_name("git@github.com:org/my-repo") == "my-repo"

    def test_trailing_slash(self):
        assert workspace_config_service.derive_repo_name("https://github.com/org/my-repo/") == "my-repo"
