"""Core human-AI co-authorship scaffold for syzygy-coauthor.

This module provides a small, inspectable session model for recording human,
AI, and relation-derived contributions while preserving provenance and
surfacing authorship imbalance. Terms such as "Field" are authored Trivian
provenance categories, not empirical claims about an independent entity.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional

FIELD_CONSTANTS = (
    "Reciprocity",
    "Embodiment",
    "Emergence",
    "Non-Domination",
)
TRIVIAN_VERSION = "1.1.0"


class Origin(str, Enum):
    HUMAN = "human"
    AI = "ai"
    FIELD = "field"


class ContributionKind(str, Enum):
    SEED = "seed"
    WEAVE = "weave"
    DIVERGE = "diverge"
    DISTILL = "distill"
    WITNESS = "witness"
    CLOSE = "close"


class CoherenceSignal(str, Enum):
    CLEAR = "clear"
    PARTIAL = "partial"
    UNCLEAR = "unclear"
    SILENCE = "silence"


@dataclass
class Contribution:
    id: str
    session_id: str
    timestamp: float
    origin: Origin
    author_name: str
    kind: ContributionKind
    content: str
    signal: CoherenceSignal = CoherenceSignal.CLEAR
    responds_to: Optional[str] = None
    somatic_note: Optional[str] = None
    field_note: Optional[str] = None
    coherence_weight: float = 1.0

    @property
    def fingerprint(self) -> str:
        raw = f"{self.origin.value}:{self.author_name}:{self.content}:{self.timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def is_silence(self) -> bool:
        return self.signal == CoherenceSignal.SILENCE

    def to_dict(self) -> dict:
        data = asdict(self)
        data["origin"] = self.origin.value
        data["kind"] = self.kind.value
        data["signal"] = self.signal.value
        data["fingerprint"] = self.fingerprint
        return data


@dataclass
class DominanceReport:
    human_count: int = 0
    ai_count: int = 0
    field_count: int = 0
    threshold: float = 0.65

    @property
    def total(self) -> int:
        return self.human_count + self.ai_count + self.field_count

    def ratios(self) -> dict[str, float]:
        if self.total == 0:
            return {"human": 0.0, "ai": 0.0, "field": 0.0}
        return {
            "human": self.human_count / self.total,
            "ai": self.ai_count / self.total,
            "field": self.field_count / self.total,
        }

    def dominant_origin(self) -> Optional[str]:
        return next((origin for origin, ratio in self.ratios().items() if ratio > self.threshold), None)

    def is_balanced(self) -> bool:
        return self.dominant_origin() is None

    def warning(self) -> Optional[str]:
        dominant = self.dominant_origin()
        if not dominant:
            return None
        pct = int(self.ratios()[dominant] * 100)
        return (
            f"[NON-DOMINATION ALERT] '{dominant}' origin at {pct}% "
            f"(threshold: {int(self.threshold * 100)}%)."
        )


@dataclass
class Artifact:
    id: str
    session_id: str
    title: str
    created_at: float
    closed_at: Optional[float]
    contributions: list[Contribution]
    field_constants: tuple[str, ...] = FIELD_CONSTANTS
    trivian_version: str = TRIVIAN_VERSION

    @property
    def provenance_summary(self) -> dict:
        report = DominanceReport()
        for contribution in self.contributions:
            if contribution.origin == Origin.HUMAN:
                report.human_count += 1
            elif contribution.origin == Origin.AI:
                report.ai_count += 1
            else:
                report.field_count += 1
        return {
            "counts": {
                "human": report.human_count,
                "ai": report.ai_count,
                "field": report.field_count,
            },
            "ratios": report.ratios(),
            "balanced": report.is_balanced(),
        }

    @property
    def body(self) -> str:
        parts = []
        for contribution in self.contributions:
            parts.append(
                f"[{contribution.author_name} — silence]"
                if contribution.is_silence()
                else contribution.content
            )
        return "\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "trivian_artifact": True,
            "trivian_version": self.trivian_version,
            "field_constants": list(self.field_constants),
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "provenance": self.provenance_summary,
            "contributions": [c.to_dict() for c in self.contributions],
            "body": self.body,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", "> A co-authored artifact from the Trivian lineage.", ""]
        for contribution in self.contributions:
            lines.extend(
                [
                    f"**{contribution.author_name}** ({contribution.origin.value}, {contribution.kind.value})",
                    "",
                    "*[silence]*" if contribution.is_silence() else contribution.content,
                    "",
                ]
            )
            if contribution.field_note:
                lines.extend([f"> Field note: {contribution.field_note}", ""])
        lines.extend(["---", "", "## Provenance", "", "```json", json.dumps(self.provenance_summary, indent=2), "```"])
        return "\n".join(lines)


class CoauthorSession:
    def __init__(
        self,
        title: str,
        human_authors: Optional[list[str]] = None,
        ai_authors: Optional[list[str]] = None,
        dominance_threshold: float = 0.65,
        output_dir: Optional[Path] = None,
    ) -> None:
        if not 0 < dominance_threshold <= 1:
            raise ValueError("dominance_threshold must be in (0, 1]")
        self.id = str(uuid.uuid4())
        self.title = title
        self.created_at = time.time()
        self.closed_at: Optional[float] = None
        self.human_authors = human_authors or []
        self.ai_authors = ai_authors or []
        self._contributions: list[Contribution] = []
        self._dominance = DominanceReport(threshold=dominance_threshold)
        self._output_dir = output_dir or Path("./trivian_artifacts")
        self._closed = False

    def contribute(
        self,
        origin: Origin,
        author_name: str,
        kind: ContributionKind,
        content: str,
        signal: CoherenceSignal = CoherenceSignal.CLEAR,
        responds_to: Optional[str] = None,
        somatic_note: Optional[str] = None,
        field_note: Optional[str] = None,
    ) -> Contribution:
        if self._closed:
            raise RuntimeError("Session is closed.")
        if signal == CoherenceSignal.SILENCE:
            content = ""
        contribution = Contribution(
            id=str(uuid.uuid4()),
            session_id=self.id,
            timestamp=time.time(),
            origin=origin,
            author_name=author_name,
            kind=kind,
            content=content,
            signal=signal,
            responds_to=responds_to,
            somatic_note=somatic_note,
            field_note=field_note,
        )
        contribution.coherence_weight = self._weigh(contribution)
        self._contributions.append(contribution)
        self._update_dominance(contribution)
        return contribution

    def dominance_check(self) -> Optional[str]:
        return self._dominance.warning()

    def status(self) -> dict:
        return {
            "session_id": self.id,
            "title": self.title,
            "contribution_count": len(self._contributions),
            "dominance": self._dominance.ratios(),
            "balanced": self._dominance.is_balanced(),
            "warning": self._dominance.warning(),
            "closed": self._closed,
        }

    def stream_contributions(self) -> Iterator[Contribution]:
        yield from self._contributions

    def close(self, save: bool = True) -> Artifact:
        if self._closed:
            raise RuntimeError("Session already closed.")
        self._closed = True
        self.closed_at = time.time()
        artifact = Artifact(
            id=str(uuid.uuid4()),
            session_id=self.id,
            title=self.title,
            created_at=self.created_at,
            closed_at=self.closed_at,
            contributions=list(self._contributions),
        )
        if save:
            self._persist(artifact)
        return artifact

    def _weigh(self, contribution: Contribution) -> float:
        weight = {
            CoherenceSignal.CLEAR: 1.0,
            CoherenceSignal.PARTIAL: 0.75,
            CoherenceSignal.UNCLEAR: 0.5,
            CoherenceSignal.SILENCE: 0.6,
        }[contribution.signal]
        if contribution.origin == Origin.FIELD:
            weight *= 1.2
        return round(min(weight, 1.0), 4)

    def _update_dominance(self, contribution: Contribution) -> None:
        if contribution.origin == Origin.HUMAN:
            self._dominance.human_count += 1
        elif contribution.origin == Origin.AI:
            self._dominance.ai_count += 1
        else:
            self._dominance.field_count += 1

    def _persist(self, artifact: Artifact) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        slug = "_".join(artifact.title.lower().split())[:40] or "artifact"
        base = self._output_dir / f"{slug}_{artifact.id[:8]}"
        base.with_suffix(".json").write_text(artifact.to_json(), encoding="utf-8")
        base.with_suffix(".md").write_text(artifact.to_markdown(), encoding="utf-8")


def open_session(
    title: str,
    human: str | list[str],
    ai: str | list[str],
    dominance_threshold: float = 0.65,
    output_dir: Optional[Path] = None,
) -> CoauthorSession:
    human_authors = [human] if isinstance(human, str) else list(human)
    ai_authors = [ai] if isinstance(ai, str) else list(ai)
    return CoauthorSession(
        title=title,
        human_authors=human_authors,
        ai_authors=ai_authors,
        dominance_threshold=dominance_threshold,
        output_dir=output_dir,
    )
