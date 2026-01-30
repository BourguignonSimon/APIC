"""
APIC Services Module
Core business logic and workflow orchestration.
"""

# Use lazy imports to avoid import cascade issues during testing
# and to allow individual modules to be imported independently

__all__ = [
    "ConsultantGraph",
    "create_workflow",
    "StateManager",
    "get_llm",
    "get_embeddings",
]


def __getattr__(name):
    """Lazy import of module attributes."""
    if name == "ConsultantGraph":
        from .workflow import ConsultantGraph
        return ConsultantGraph
    elif name == "create_workflow":
        from .workflow import create_workflow
        return create_workflow
    elif name == "StateManager":
        from .state_manager import StateManager
        return StateManager
    elif name == "get_llm":
        from .llm_factory import get_llm
        return get_llm
    elif name == "get_embeddings":
        from .llm_factory import get_embeddings
        return get_embeddings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
