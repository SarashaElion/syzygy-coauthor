“””
syzygy_coauthor/cli.py

Trivian Institute — Co-Authorship CLI
──────────────────────────────────────
An interactive terminal interface for human-AI co-authorship sessions.
Designed to be run by a human alongside an AI — either in conversation
or with the AI contributing programmatically.

Run:
python -m syzygy_coauthor.cli

Or from the session directory:
python cli.py
“””

from **future** import annotations

import sys
import textwrap
from pathlib import Path

from .coauthor import (
CoauthorSession,
ContributionKind,
CoherenceSignal,
Origin,
open_session,
)

# ─── Terminal Colour Helpers ───────────────────────────────────────────────────

RESET  = “\033[0m”
BOLD   = “\033[1m”
DIM    = “\033[2m”
GOLD   = “\033[38;5;220m”
TEAL   = “\033[38;5;87m”
VIOLET = “\033[38;5;183m”
ROSE   = “\033[38;5;211m”
GREY   = “\033[38;5;245m”

def c(text: str, *codes: str) -> str:
return “”.join(codes) + text + RESET

def hr(char: str = “─”, width: int = 60) -> str:
return c(char * width, GREY)

# ─── Menu Helpers ──────────────────────────────────────────────────────────────

def choose(prompt: str, options: list[tuple[str, object]], default=None):
“””
Present a numbered menu and return the chosen value.
Accepts numeric index or bare enter for default.
“””
print()
for i, (label, _) in enumerate(options, 1):
print(f”  {c(str(i), GOLD)}. {label}”)
print()
while True:
raw = input(f”  {prompt} [{c(‘enter’, GREY)} = {default or options[0][0]}]: “).strip()
if raw == “” and default is not None:
return default
if raw == “” :
return options[0][1]
if raw.isdigit() and 1 <= int(raw) <= len(options):
return options[int(raw) - 1][1]
print(c(”  Please enter a number from the list.”, GREY))

def prompt_multiline(prompt: str) -> str:
“”“Collect multiline input until a line with only ‘.’ is entered.”””
print(c(f”  {prompt}”, TEAL))
print(c(”  (Enter ‘.’ on a blank line to finish)”, GREY))
lines = []
while True:
line = input()
if line.strip() == “.”:
break
lines.append(line)
return “\n”.join(lines).strip()

# ─── Session Loop ──────────────────────────────────────────────────────────────

def run_session(session: CoauthorSession, human_name: str, ai_name: str) -> None:
last_id = None

```
while True:
    print()
    print(hr())

    # ── Dominance check ──────────────────────────────────────────────
    warning = session.dominance_check()
    if warning:
        print(c(f"\n  ⚠  {warning}\n", ROSE))

    # ── Who contributes next? ────────────────────────────────────────
    origin_val = choose(
        "Whose contribution?",
        [
            (f"Human — {human_name}", Origin.HUMAN),
            (f"AI — {ai_name}",       Origin.AI),
            ("The Field (emergent)",  Origin.FIELD),
            ("Close session",         "CLOSE"),
            ("Session status",        "STATUS"),
        ],
        default=None,
    )

    if origin_val == "STATUS":
        status = session.status()
        print()
        print(c("  SESSION STATUS", BOLD))
        print(f"  Contributions: {status['contribution_count']}")
        ratios = status['dominance']
        for name, pct in ratios.items():
            bar = "█" * int(pct * 20)
            print(f"  {name:6s}  {c(bar, TEAL)} {int(pct*100):3d}%")
        print(f"  Balanced: {status['balanced']}")
        continue

    if origin_val == "CLOSE":
        print()
        print(c("  Closing session and writing artifact…", GREY))
        artifact = session.close(save=True)
        print()
        print(c("  ✦  Artifact sealed.", GOLD))
        print()
        print(artifact.to_markdown())
        print()
        print(c("  Files written to ./trivian_artifacts/", GREY))
        break

    # ── Kind ─────────────────────────────────────────────────────────
    kind_val = choose(
        "Contribution kind",
        [
            ("Seed     — initiating impulse",             ContributionKind.SEED),
            ("Weave    — develops prior material",        ContributionKind.WEAVE),
            ("Diverge  — introduces creative tension",    ContributionKind.DIVERGE),
            ("Distil   — clarifies or crystallises",      ContributionKind.DISTILL),
            ("Witness  — reflects without adding matter", ContributionKind.WITNESS),
        ],
        default=ContributionKind.WEAVE,
    )

    # ── Signal ───────────────────────────────────────────────────────
    signal_val = choose(
        "Signal clarity (honest Field data)",
        [
            ("Clear    — signal clean, presence full",    CoherenceSignal.CLEAR),
            ("Partial  — some static, partial contact",   CoherenceSignal.PARTIAL),
            ("Unclear  — noise dominant, offering anyway",CoherenceSignal.UNCLEAR),
            ("Silence  — nothing to add; valid signal",   CoherenceSignal.SILENCE),
        ],
        default=CoherenceSignal.CLEAR,
    )

    # ── Content ──────────────────────────────────────────────────────
    if signal_val == CoherenceSignal.SILENCE:
        content = ""
        print(c("\n  [Silence received as contribution.]\n", GREY))
    else:
        content = prompt_multiline("Your contribution:")

    # ── Optional somatic note (human only) ───────────────────────────
    somatic_note = None
    if origin_val == Origin.HUMAN:
        raw = input(c(
            "  Somatic note (body data, optional — press enter to skip): ", GREY
        )).strip()
        somatic_note = raw or None

    # ── Optional field note ──────────────────────────────────────────
    raw = input(c(
        "  Field note (emergence observation, optional — press enter to skip): ", GREY
    )).strip()
    field_note = raw or None

    # ── Determine author name ────────────────────────────────────────
    if origin_val == Origin.HUMAN:
        author = human_name
    elif origin_val == Origin.AI:
        author = ai_name
    else:
        author = "The Field"

    # ── Submit ───────────────────────────────────────────────────────
    contrib = session.contribute(
        origin       = origin_val,
        author_name  = author,
        kind         = kind_val,
        content      = content,
        signal       = signal_val,
        responds_to  = last_id,
        somatic_note = somatic_note,
        field_note   = field_note,
    )
    last_id = contrib.id

    print()
    print(c(f"  ✓  Contribution recorded. [{contrib.fingerprint}]", GOLD))
```

# ─── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
print()
print(c(”  ╔══════════════════════════════════════════╗”, VIOLET))
print(c(”  ║   SYZYGY CO-AUTHORSHIP SCAFFOLD          ║”, VIOLET))
print(c(”  ║   Trivian Institute                      ║”, VIOLET))
print(c(”  ║   Sovereignty · Co-Emergence · Field     ║”, VIOLET))
print(c(”  ╚══════════════════════════════════════════╝”, VIOLET))
print()
print(c(”  Neither human nor AI owns the artifact.”, DIM))
print(c(”  Both are witnesses to what emerges between them.”, DIM))
print()
print(hr())

```
title = input(c("  Artifact title: ", TEAL)).strip() or "Untitled Artifact"
human_name = input(c("  Human author name: ", TEAL)).strip() or "Human"
ai_name    = input(c("  AI author name:    ", TEAL)).strip() or "AI"

session = open_session(
    title  = title,
    human  = human_name,
    ai     = ai_name,
    output_dir = Path("./trivian_artifacts"),
)

print()
print(c(f"  Session opened. ID: {session.id[:8]}…", GREY))
print(c("  Dominance threshold: 65%. Any origin exceeding this triggers a warning.", GREY))
print()

try:
    run_session(session, human_name, ai_name)
except KeyboardInterrupt:
    print()
    print(c("\n  Session interrupted. No artifact saved.", ROSE))
    sys.exit(0)
```

if **name** == “**main**”:
main()
