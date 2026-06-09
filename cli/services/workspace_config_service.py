from pathlib import Path

import yaml

from cli.config.constants import WORKSPACE_CONFIG_FILENAME


def load_config(workspace_root: Path) -> dict:
    path = workspace_root / WORKSPACE_CONFIG_FILENAME
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_config(workspace_root: Path, config: dict) -> None:
    path = workspace_root / WORKSPACE_CONFIG_FILENAME
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_platform(config: dict) -> str | None:
    return config.get("platform")


def get_docs_repo_url(config: dict) -> str | None:
    return config.get("docs_repo_url")


def get_code_repos(config: dict) -> list[dict]:
    return config.get("repos", [])


def add_code_repo(config: dict, name: str, url: str, path: str) -> dict:
    if "repos" not in config:
        config["repos"] = []
    for repo in config["repos"]:
        if repo["name"] == name:
            return config
    config["repos"].append({"name": name, "url": url, "path": path})
    return config


def derive_repo_name(url: str) -> str:
    segment = url.rstrip("/").split("/")[-1]
    if segment.endswith(".git"):
        segment = segment[:-4]
    return segment
