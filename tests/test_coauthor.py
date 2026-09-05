import tempfile
import unittest
from pathlib import Path

from syzygy_coauthor import (
    CoherenceSignal,
    ContributionKind,
    Origin,
    open_session,
)


class CoauthorTests(unittest.TestCase):
    def test_session_records_provenance_and_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = open_session(
                "Test Artifact",
                human="Human",
                ai="AI",
                output_dir=Path(tmp),
            )
            session.contribute(Origin.HUMAN, "Human", ContributionKind.SEED, "A")
            session.contribute(Origin.AI, "AI", ContributionKind.WEAVE, "B")
            artifact = session.close(save=False)

            self.assertEqual(artifact.provenance_summary["counts"]["human"], 1)
            self.assertEqual(artifact.provenance_summary["counts"]["ai"], 1)
            self.assertIn("A", artifact.body)
            self.assertIn("B", artifact.body)

    def test_silence_is_preserved_without_content(self):
        session = open_session("Silence", human="H", ai="A")
        contribution = session.contribute(
            Origin.AI,
            "A",
            ContributionKind.WITNESS,
            "ignored",
            signal=CoherenceSignal.SILENCE,
        )
        self.assertEqual(contribution.content, "")
        self.assertTrue(contribution.is_silence())

    def test_dominance_warning_surfaces(self):
        session = open_session("Dominance", human="H", ai="A", dominance_threshold=0.65)
        session.contribute(Origin.HUMAN, "H", ContributionKind.SEED, "1")
        session.contribute(Origin.HUMAN, "H", ContributionKind.WEAVE, "2")
        session.contribute(Origin.AI, "A", ContributionKind.WEAVE, "3")
        self.assertIsNotNone(session.dominance_check())

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            open_session("Bad", human="H", ai="A", dominance_threshold=0)


if __name__ == "__main__":
    unittest.main()
