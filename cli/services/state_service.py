import re
from pathlib import Path

from cli.exceptions import StateNotFoundError


def find_state_file(docs_dir: Path, project: str) -> Path | None:
    state_path = docs_dir / project / "aidlc-state.md"
    if state_path.exists():
        return state_path
    return None


def parse_state(state_path: Path) -> dict:
    if not state_path.exists():
        raise StateNotFoundError(f"State file not found: {state_path}")
    content = state_path.read_text()
    return {
        "project_type": _extract_field(content, "Project Type"),
        "current_stage": _extract_field(content, "Current Stage"),
        "start_date": _extract_field(content, "Start Date"),
        "stages": _parse_stages(content),
    }


def get_current_stage(state: dict) -> str:
    return state.get("current_stage", "Unknown")


def is_workflow_in_progress(state: dict) -> bool:
    for stage in state.get("stages", []):
        if stage["status"] == "in_progress":
            return True
    found_completed = False
    for stage in state.get("stages", []):
        if stage["status"] == "completed":
            found_completed = True
        elif found_completed and stage["status"] == "pending":
            return True
    return False


def get_completed_stages(state: dict) -> list[str]:
    return [s["name"] for s in state.get("stages", []) if s["status"] == "completed"]


def _extract_field(content: str, field_name: str) -> str | None:
    pattern = rf"\*\*{re.escape(field_name)}\*\*:\s*(.+)"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else None


def _parse_stages(content: str) -> list[dict]:
    stages = []
    for match in re.finditer(r"- \[([x ])\] (.+)", content):
        checkbox, text = match.group(1), match.group(2)
        name = text.split("—")[0].strip()
        if checkbox == "x":
            status = "completed"
        elif "SKIP" in text.upper():
            status = "skipped"
        elif "In Progress" in text or "EXECUTE" in text:
            status = "in_progress"
        else:
            status = "pending"
        stages.append({"name": name, "status": status})
    return stages
