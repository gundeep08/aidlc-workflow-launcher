AIDLC_WORKFLOWS_REPO_OWNER = "awslabs"
AIDLC_WORKFLOWS_REPO_NAME = "aidlc-workflows"
WORKSPACE_CONFIG_FILENAME = "workspace-config.yml"
CODE_DIR = "code"
DOCS_DIR = "docs"
AIDLC_DOCS_SUBDIR = "aidlc-docs"
RE_SKILLS_SUBDIR = "re-skills"

PLATFORM_MAPPINGS = {
    "amazon-q": {
        "display_name": "Amazon Q Developer",
        "rules_path": ".amazonq/rules/aws-aidlc-rules/",
        "details_path": ".amazonq/aws-aidlc-rule-details/",
        "single_file": False,
    },
    "kiro": {
        "display_name": "Kiro",
        "rules_path": ".kiro/steering/aws-aidlc-rules/",
        "details_path": ".kiro/aws-aidlc-rule-details/",
        "single_file": False,
    },
    "cursor": {
        "display_name": "Cursor",
        "rules_path": ".cursor/rules/ai-dlc-workflow.mdc",
        "details_path": ".aidlc-rule-details/",
        "single_file": True,
    },
    "cline": {
        "display_name": "Cline",
        "rules_path": ".clinerules/core-workflow.md",
        "details_path": ".aidlc-rule-details/",
        "single_file": True,
    },
    "claude-code": {
        "display_name": "Claude Code",
        "rules_path": "CLAUDE.md",
        "details_path": ".aidlc-rule-details/",
        "single_file": True,
    },
    "github-copilot": {
        "display_name": "GitHub Copilot",
        "rules_path": ".github/copilot-instructions.md",
        "details_path": ".aidlc-rule-details/",
        "single_file": True,
    },
}
