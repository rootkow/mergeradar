from __future__ import annotations


class MergeRadarError(Exception):
    """Base exception for MergeRadar errors."""


class ConfigError(MergeRadarError):
    """Raised when MergeRadar configuration is invalid."""


class DiffLoaderError(MergeRadarError):
    """Raised when a Git diff cannot be loaded or contains no changes."""
