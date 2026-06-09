class AidlcError(Exception):
    """Base exception for aidlc CLI."""


class GitNotInstalledError(AidlcError):
    """Git binary not found on PATH."""


class GitCloneError(AidlcError):
    """Git clone operation failed."""


class GitHubReleaseError(AidlcError):
    """GitHub API call failed or no releases found."""


class NetworkError(AidlcError):
    """No internet connection or request failed."""


class PlatformNotConfiguredError(AidlcError):
    """No platform selected yet."""


class ConfigNotFoundError(AidlcError):
    """workspace-config.yml missing."""


class StateNotFoundError(AidlcError):
    """aidlc-state.md not found for project."""


class NoWorkflowInProgressError(AidlcError):
    """Nothing to resume."""
