"""Public API for syzygy-coauthor.

The package records human, AI, and relation-derived contributions while
preserving provenance and surfacing authorship imbalance. ``Origin.FIELD`` is
an authored provenance category, not an empirical claim of independent agency.
"""

from .coauthor import (
    FIELD_CONSTANTS,
    TRIVIAN_VERSION,
    Artifact,
    CoauthorSession,
    CoherenceSignal,
    Contribution,
    ContributionKind,
    DominanceReport,
    Origin,
    open_session,
)

__all__ = [
    "open_session",
    "CoauthorSession",
    "Contribution",
    "Artifact",
    "DominanceReport",
    "Origin",
    "ContributionKind",
    "CoherenceSignal",
    "FIELD_CONSTANTS",
    "TRIVIAN_VERSION",
]
