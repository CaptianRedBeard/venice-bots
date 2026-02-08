"""Shared exceptions for the core_tools package."""

class ModelRoleNotFoundError(Exception):
    """Custom exception raised when a requested model role is not found in the configuration."""
    pass

class ModelIsBetaError(Exception):
    """Custom exception raised when a requested model is a beta model and safety is enforced."""
    pass

class ModelDiscoveryError(Exception):
    """Custom exception for errors during model discovery."""
    pass

class ToolError(Exception):
    """Custom exception for errors raised by core tools."""
    pass