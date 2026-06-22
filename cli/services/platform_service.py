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


def get_prompts_path(platform: str, workspace_root: Path) -> Path:
    _validate_platform(platform)
    raw = PLATFORM_MAPPINGS[platform]["prompts_path"]
    if PLATFORM_MAPPINGS[platform]["prompts_native"]:
        return Path(raw).expanduser()
    return workspace_root / raw


def is_prompts_native(platform: str) -> bool:
    _validate_platform(platform)
    return PLATFORM_MAPPINGS[platform]["prompts_native"]


def get_prompt_command(platform: str, prompt_name: str) -> str | None:
    """Return the IDE command to invoke a prompt, or None if not natively supported."""
    _validate_platform(platform)
    if not PLATFORM_MAPPINGS[platform]["prompts_native"]:
        return None
    prefix = "/" if platform == "kiro" else "@"
    stem = prompt_name.removesuffix(".md")
    return f"{prefix}{stem}"


def write_resolved_prompts(platform: str, docs_prompts_dir: Path, workspace_root: Path, substitutions: dict) -> None:
    """Write context-sensitive prompts with placeholders substituted to the platform prompts dir."""
    _validate_platform(platform)
    if not docs_prompts_dir.exists():
        return
    target_dir = get_prompts_path(platform, workspace_root)
    target_dir.mkdir(parents=True, exist_ok=True)
    for src_file in docs_prompts_dir.glob("*.md"):
        content = src_file.read_text()
        for key, value in substitutions.items():
            content = content.replace(f"{{{key}}}", value)
        (target_dir / src_file.name).write_text(content)


def sync_prompts(platform: str, docs_prompts_dir: Path, workspace_root: Path) -> dict:
    """Merge team prompts into the platform prompt location.

    Returns a dict with keys 'installed' (list) and 'conflicts' (list).
    - installed: prompts copied (did not exist locally)
    - conflicts: prompts skipped because a local copy exists with different content
    """
    result = {"installed": [], "conflicts": []}
    if not docs_prompts_dir.exists():
        return result

    target_dir = get_prompts_path(platform, workspace_root)
    target_dir.mkdir(parents=True, exist_ok=True)

    for src_file in sorted(docs_prompts_dir.glob("*.md")):
        dest_file = target_dir / src_file.name
        src_content = src_file.read_text()
        if not dest_file.exists():
            dest_file.write_text(src_content)
            result["installed"].append(src_file.name)
        elif dest_file.read_text() != src_content:
            result["conflicts"].append(src_file.name)
        # identical content — silently skip

    return result


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
