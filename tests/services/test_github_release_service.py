import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli.services import github_release_service
from cli.exceptions import GitHubReleaseError, NetworkError


class TestGetLatestReleaseInfo:
    @patch("requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"tag_name": "v0.1.8", "zipball_url": "https://example.com/zip"},
        )
        result = github_release_service.get_latest_release_info("awslabs", "aidlc-workflows")
        assert result == {"tag": "v0.1.8", "download_url": "https://example.com/zip"}

    @patch("requests.get")
    def test_http_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)
        with pytest.raises(GitHubReleaseError):
            github_release_service.get_latest_release_info("awslabs", "aidlc-workflows")

    @patch("requests.get", side_effect=Exception("ConnectionError"))
    def test_network_error(self, mock_get):
        from requests import ConnectionError
        with patch("requests.get", side_effect=ConnectionError):
            with pytest.raises(NetworkError):
                github_release_service.get_latest_release_info("awslabs", "aidlc-workflows")


class TestDownloadReleaseZip:
    @patch("requests.get")
    def test_success(self, mock_get, tmp_path):
        mock_resp = MagicMock(status_code=200)
        mock_resp.iter_content.return_value = [b"data"]
        mock_get.return_value = mock_resp
        target = tmp_path / "release.zip"
        result = github_release_service.download_release_zip("https://example.com/zip", target)
        assert result == target
        assert target.exists()

    @patch("requests.get")
    def test_http_error(self, mock_get, tmp_path):
        mock_get.return_value = MagicMock(status_code=500)
        with pytest.raises(NetworkError):
            github_release_service.download_release_zip("https://example.com/zip", tmp_path / "f.zip")


class TestExtractRules:
    def test_extracts_top_level_dir(self, tmp_path):
        zip_path = tmp_path / "release.zip"
        content_dir = "aidlc-workflows-abc123"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(f"{content_dir}/rules/core.md", "# rules")
            zf.writestr(f"{content_dir}/rule-details/detail.md", "# details")
        extract_to = tmp_path / "extracted"
        extract_to.mkdir()
        result = github_release_service.extract_rules(zip_path, extract_to)
        assert result.name == content_dir

    def test_raises_on_empty_zip(self, tmp_path):
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            pass
        extract_to = tmp_path / "extracted"
        extract_to.mkdir()
        with pytest.raises(GitHubReleaseError):
            github_release_service.extract_rules(zip_path, extract_to)
