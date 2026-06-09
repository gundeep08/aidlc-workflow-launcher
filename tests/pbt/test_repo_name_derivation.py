from hypothesis import given, strategies as st

from cli.services.workspace_config_service import derive_repo_name


ssh_urls = st.from_regex(
    r"git@[a-z]+\.[a-z]+\.[a-z]+:[a-z]+/[a-z][a-z0-9\-]{1,20}\.git",
    fullmatch=True,
)

https_urls = st.from_regex(
    r"https://[a-z]+\.[a-z]+/[a-z]+/[a-z][a-z0-9\-]{1,20}\.git",
    fullmatch=True,
)

urls_without_git = st.from_regex(
    r"git@[a-z]+\.[a-z]+:[a-z]+/[a-z][a-z0-9\-]{1,20}",
    fullmatch=True,
)

all_urls = st.one_of(ssh_urls, https_urls, urls_without_git)


class TestDeriveRepoNamePBT:
    @given(url=all_urls)
    def test_always_returns_non_empty_string(self, url):
        result = derive_repo_name(url)
        assert isinstance(result, str)
        assert len(result) > 0

    @given(url=all_urls)
    def test_never_contains_git_suffix(self, url):
        result = derive_repo_name(url)
        assert not result.endswith(".git")

    @given(url=all_urls)
    def test_never_contains_slashes(self, url):
        result = derive_repo_name(url)
        assert "/" not in result
        assert "\\" not in result

    @given(url=ssh_urls)
    def test_ssh_url_produces_last_segment(self, url):
        result = derive_repo_name(url)
        expected = url.split("/")[-1].replace(".git", "")
        assert result == expected

    @given(url=https_urls)
    def test_https_url_produces_last_segment(self, url):
        result = derive_repo_name(url)
        expected = url.rstrip("/").split("/")[-1].replace(".git", "")
        assert result == expected
