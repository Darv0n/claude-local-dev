"""Error hierarchy — names describe structural causes, not symptoms."""

from __future__ import annotations


class CldError(Exception):
    """Base error for claude-local-dev."""


class MarketplaceNotInitialized(CldError):
    """local-dev marketplace directory structure does not exist."""


class PluginNotFound(CldError):
    """The specified path does not contain a valid plugin."""


class PluginAlreadyRegistered(CldError):
    """A plugin with this name is already registered in local-dev."""


class PluginNotRegistered(CldError):
    """No plugin with this name is registered in local-dev."""


class JunctionError(CldError):
    """Failed to create or remove a filesystem junction/symlink."""


class BrokenJunction(CldError):
    """Junction exists but its target is missing or inaccessible."""


class RegistryCorrupted(CldError):
    """A JSON registry file has unexpected structure."""
