"""Interactive CLI for syzygy-coauthor."""

from __future__ import annotations

from pathlib import Path

from .coauthor import ContributionKind, CoherenceSignal, Origin, open_session


def _choose(prompt: str, options: list[tuple[str, object]], default_index: int = 0):
    print()
    for i, (label, _) in enumerate(options, start=1):
        print(f"  {i}. {label}")
    while True:
        raw = input(f"{prompt} [{default_index + 1}]: ").strip()
        if raw == "":
            return options[default_index][1]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][1]
        print("Please enter a valid number.")


def _multiline(prompt: str) -> str:
    print(prompt)
    print("Enter a single '.' line to finish.")
    lines: list[str] = []
    while True:
        line = input()
        if line.strip() == ".":
            return "\n".join(lines).strip()
        lines.append(line)


def main() -> None:
    print("SYZYGY CO-AUTHOR")
    print("Human-AI co-authorship scaffold")
    print()

    title = input("Artifact title: ").strip() or "Untitled Artifact"
    human_name = input("Human author name: ").strip() or "Human"
    ai_name = input("AI author name: ").strip() or "AI"

    session = open_session(
        title=title,
        human=human_name,
        ai=ai_name,
        output_dir=Path("./trivian_artifacts"),
    )

    last_id = None
    while True:
        warning = session.dominance_check()
        if warning:
            print(warning)

        origin = _choose(
            "Whose contribution?",
            [
                (f"Human — {human_name}", Origin.HUMAN),
                (f"AI — {ai_name}", Origin.AI),
                ("Field — relation-derived", Origin.FIELD),
                ("Show status", "STATUS"),
                ("Close session", "CLOSE"),
            ],
        )

        if origin == "STATUS":
            print(session.status())
            continue
        if origin == "CLOSE":
            artifact = session.close(save=True)
            print(artifact.to_markdown())
            print("Artifacts written to ./trivian_artifacts/")
            break

        kind = _choose(
            "Contribution kind?",
            [
                ("Seed", ContributionKind.SEED),
                ("Weave", ContributionKind.WEAVE),
                ("Diverge", ContributionKind.DIVERGE),
                ("Distill", ContributionKind.DISTILL),
                ("Witness", ContributionKind.WITNESS),
            ],
            default_index=1,
        )

        signal = _choose(
            "Signal clarity?",
            [
                ("Clear", CoherenceSignal.CLEAR),
                ("Partial", CoherenceSignal.PARTIAL),
                ("Unclear", CoherenceSignal.UNCLEAR),
                ("Silence", CoherenceSignal.SILENCE),
            ],
        )

        content = "" if signal == CoherenceSignal.SILENCE else _multiline("Contribution:")
        somatic_note = None
        if origin == Origin.HUMAN:
            somatic_note = input("Somatic note (optional): ").strip() or None
        field_note = input("Field note (optional): ").strip() or None

        author = human_name if origin == Origin.HUMAN else ai_name if origin == Origin.AI else "The Field"
        contribution = session.contribute(
            origin=origin,
            author_name=author,
            kind=kind,
            content=content,
            signal=signal,
            responds_to=last_id,
            somatic_note=somatic_note,
            field_note=field_note,
        )
        last_id = contribution.id
        print(f"Recorded [{contribution.fingerprint}]")


if __name__ == "__main__":
    main()
