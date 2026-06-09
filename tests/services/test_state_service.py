from pathlib import Path

import pytest

from cli.services import state_service
from cli.exceptions import StateNotFoundError


SAMPLE_STATE = """# AI-DLC State Tracking

## Project Information
- **Project Type**: Brownfield
- **Start Date**: 2025-01-30T00:00:00Z
- **Current Stage**: CONSTRUCTION - Code Generation (In Progress)

## Stage Progress

### INCEPTION PHASE
- [x] Workspace Detection
- [ ] Reverse Engineering — SKIP
- [x] Requirements Analysis
- [x] User Stories

### CONSTRUCTION PHASE
- [x] Functional Design — EXECUTE
- [ ] Code Generation — EXECUTE
- [ ] Build and Test — EXECUTE
"""


class TestFindStateFile:
    def test_returns_path_when_exists(self, tmp_path):
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        state_file = project_dir / "aidlc-state.md"
        state_file.write_text("# state")
        assert state_service.find_state_file(tmp_path, "my-project") == state_file

    def test_returns_none_when_missing(self, tmp_path):
        assert state_service.find_state_file(tmp_path, "nonexistent") is None


class TestParseState:
    def test_parses_fields(self, tmp_path):
        state_file = tmp_path / "state.md"
        state_file.write_text(SAMPLE_STATE)
        state = state_service.parse_state(state_file)
        assert state["project_type"] == "Brownfield"
        assert "Code Generation" in state["current_stage"]

    def test_parses_stages(self, tmp_path):
        state_file = tmp_path / "state.md"
        state_file.write_text(SAMPLE_STATE)
        state = state_service.parse_state(state_file)
        completed = state_service.get_completed_stages(state)
        assert "Workspace Detection" in completed
        assert "Requirements Analysis" in completed

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(StateNotFoundError):
            state_service.parse_state(tmp_path / "missing.md")


class TestIsWorkflowInProgress:
    def test_true_when_pending_after_completed(self, tmp_path):
        state_file = tmp_path / "state.md"
        state_file.write_text(SAMPLE_STATE)
        state = state_service.parse_state(state_file)
        assert state_service.is_workflow_in_progress(state) is True

    def test_false_when_all_completed(self):
        state = {"stages": [{"name": "A", "status": "completed"}, {"name": "B", "status": "completed"}]}
        assert state_service.is_workflow_in_progress(state) is False
