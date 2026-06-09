import shutil
from pathlib import Path

from cli.config.constants import PLATFORM_MAPPINGS
from cli.exceptions import PlatformNotConfiguredError


def get_supported_platforms() -> list[str]:
    return list(PLATFORM_MAPPINGS.keys())


def get_display_names() -> list[tuple[str, str]]:
    return [(k, v["display_name"]) for k, v in PLATFORM_MAPPINGS.items()]


def get_rules_path(platform: str) -> str:
    _validate_platform(platform)
    return PLATFORM_MAPPINGS[platform]["rules_path"]


def get_rule_details_path(platform: str) -> str:
    _validate_platform(platform)
    return PLATFORM_MAPPINGS[platform]["details_path"]


def is_single_file_platform(platform: str) -> bool:
    _validate_platform(platform)
    return PLATFORM_MAPPINGS[platform]["single_file"]


def place_rules(platform: str, rules_source: Path, workspace_root: Path) -> None:
    _validate_platform(platform)
    mapping = PLATFORM_MAPPINGS[platform]
    rules_target = workspace_root / mapping["rules_path"]
    details_target = workspace_root / mapping["details_path"]

    # Locate aidlc-rules directory within the extracted release
    aidlc_rules_dir = rules_source / "aidlc-rules"
    if not aidlc_rules_dir.exists():
        aidlc_rules_dir = rules_source  # fallback for older releases

    rules_src = aidlc_rules_dir / "aws-aidlc-rules"
    details_src = aidlc_rules_dir / "aws-aidlc-rule-details"

    if mapping["single_file"]:
        _place_single_file(rules_src, rules_target)
    else:
        _place_directory(rules_src, rules_target)

    _place_directory(details_src, details_target)


def detect_current_platform(workspace_root: Path) -> str | None:
    for platform, mapping in PLATFORM_MAPPINGS.items():
        target = workspace_root / mapping["rules_path"]
        if target.exists():
            return platform
    return None


def _place_single_file(rules_source: Path, target_file: Path) -> None:
    target_file.parent.mkdir(parents=True, exist_ok=True)
    if not rules_source.exists():
        return
    content_parts = []
    for f in sorted(rules_source.rglob("*.md")):
        content_parts.append(f.read_text())
    target_file.write_text("\n\n".join(content_parts))


def _place_directory(source: Path, target: Path) -> None:
    if not source.exists():
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _validate_platform(platform: str) -> None:
    if platform not in PLATFORM_MAPPINGS:
        raise PlatformNotConfiguredError(
            f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORM_MAPPINGS.keys())}"
        )
