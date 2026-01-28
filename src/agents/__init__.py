"""
APIC Agents Module
Contains all agent implementations for the Consultant Graph nodes.
"""

__all__ = [
    "BaseAgent",
    "get_llm",
    "IngestionAgent",
    "HypothesisGeneratorAgent",
    "InterviewArchitectAgent",
    "GapAnalystAgent",
    "SolutionArchitectAgent",
    "ReportingAgent",
]


def __getattr__(name):
    """Lazy import of module attributes to avoid import cascade issues."""
    if name == "BaseAgent":
        from .base import BaseAgent
        return BaseAgent
    elif name == "get_llm":
        from .base import get_llm
        return get_llm
    elif name == "IngestionAgent":
        from .ingestion import IngestionAgent
        return IngestionAgent
    elif name == "HypothesisGeneratorAgent":
        from .hypothesis import HypothesisGeneratorAgent
        return HypothesisGeneratorAgent
    elif name == "InterviewArchitectAgent":
        from .interview import InterviewArchitectAgent
        return InterviewArchitectAgent
    elif name == "GapAnalystAgent":
        from .gap_analyst import GapAnalystAgent
        return GapAnalystAgent
    elif name == "SolutionArchitectAgent":
        from .solution import SolutionArchitectAgent
        return SolutionArchitectAgent
    elif name == "ReportingAgent":
        from .reporting import ReportingAgent
        return ReportingAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
