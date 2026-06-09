from pathlib import Path

import pytest

from cli.services import platform_service
from cli.exceptions import PlatformNotConfiguredError


class TestGetSupportedPlatforms:
    def test_returns_six_platforms(self):
        platforms = platform_service.get_supported_platforms()
        assert len(platforms) == 6
        assert "amazon-q" in platforms
        assert "cursor" in platforms


class TestGetRulesPath:
    def test_amazon_q(self):
        assert platform_service.get_rules_path("amazon-q") == ".amazonq/rules/aws-aidlc-rules/"

    def test_invalid_platform_raises(self):
        with pytest.raises(PlatformNotConfiguredError):
            platform_service.get_rules_path("invalid")


class TestIsSingleFilePlatform:
    def test_amazon_q_is_multi_file(self):
        assert platform_service.is_single_file_platform("amazon-q") is False

    def test_cursor_is_single_file(self):
        assert platform_service.is_single_file_platform("cursor") is True


class TestPlaceRules:
    def test_multi_file_platform(self, tmp_path):
        source = tmp_path / "source"
        (source / "rules").mkdir(parents=True)
        (source / "rules" / "core.md").write_text("# core")
        (source / "rule-details").mkdir()
        (source / "rule-details" / "detail.md").write_text("# detail")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        platform_service.place_rules("amazon-q", source, workspace)
        assert (workspace / ".amazonq/rules/aws-aidlc-rules/core.md").exists()
        assert (workspace / ".amazonq/aws-aidlc-rule-details/detail.md").exists()

    def test_single_file_platform(self, tmp_path):
        source = tmp_path / "source"
        (source / "rules").mkdir(parents=True)
        (source / "rules" / "a.md").write_text("# part a")
        (source / "rules" / "b.md").write_text("# part b")
        (source / "rule-details").mkdir()
        (source / "rule-details" / "d.md").write_text("# detail")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        platform_service.place_rules("cursor", source, workspace)
        rules_file = workspace / ".cursor/rules/ai-dlc-workflow.mdc"
        assert rules_file.exists()
        content = rules_file.read_text()
        assert "# part a" in content
        assert "# part b" in content


class TestDetectCurrentPlatform:
    def test_detects_amazon_q(self, tmp_path):
        (tmp_path / ".amazonq/rules/aws-aidlc-rules").mkdir(parents=True)
        assert platform_service.detect_current_platform(tmp_path) == "amazon-q"

    def test_returns_none_when_no_platform(self, tmp_path):
        assert platform_service.detect_current_platform(tmp_path) is None
