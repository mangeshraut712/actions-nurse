"""Read-only Zetaris Lightning SQL integration for Actions Nurse."""

from typing import Any

__all__ = [
    "ZetarisClient",
    "get_client",
    "preflight",
    "query_ci_evidence",
    "status",
]


def __getattr__(name: str) -> Any:
    """Keep ``python -m integrations.zetaris.client`` warning-free."""
    if name in __all__:
        from . import client

        return getattr(client, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
