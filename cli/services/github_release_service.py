import subprocess
import zipfile
import os
import certifi
from pathlib import Path
import requests
from cli.exceptions import GitHubReleaseError, NetworkError


def _get_system_cert_path() -> str | None:
    """Try to find the system CA bundle for corporate SSL inspection."""
    # Check if REQUESTS_CA_BUNDLE or SSL_CERT_FILE is set
    for var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        if os.environ.get(var):
            return os.environ[var]
    return None


def _request_get(url: str, **kwargs) -> requests.Response:
    """Make a GET request, falling back to verify=False if SSL fails."""
    try:
        return requests.get(url, **kwargs)
    except (requests.ConnectionError, requests.exceptions.SSLError):
        # Corporate SSL inspection — retry without verification
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except ImportError:
            pass
        try:
            return requests.get(url, verify=False, **kwargs)
        except requests.ConnectionError:
            raise NetworkError("No internet connection. Check your network and try again.")


def get_latest_release_info(repo_owner: str, repo_name: str) -> dict:
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    resp = _request_get(url, timeout=30)
    if resp.status_code != 200:
        raise GitHubReleaseError(f"Failed to fetch release info (HTTP {resp.status_code})")
    data = resp.json()
    return {"tag": data["tag_name"], "download_url": data["zipball_url"]}


def download_release_zip(download_url: str, target_path: Path) -> Path:
    resp = _request_get(download_url, stream=True, timeout=60)
    if resp.status_code != 200:
        raise NetworkError(f"Download failed (HTTP {resp.status_code})")
    with open(target_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return target_path


def extract_rules(zip_path: Path, extract_to: Path) -> Path:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    # GitHub zips have a top-level directory named <repo>-<hash>/
    subdirs = [p for p in extract_to.iterdir() if p.is_dir()]
    if not subdirs:
        raise GitHubReleaseError("Unexpected zip structure: no top-level directory found")
    return subdirs[0]
