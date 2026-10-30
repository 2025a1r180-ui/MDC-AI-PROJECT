"""
Unit and integration tests for Emotion & Sentiment Analysis (Milestones 2 & 2B).
Validates:
1. GoEmotions mapping to Ekman 6 target classes.
2. Truncation at 4,000 characters.
3. In-memory model caching & uncertainty notice generation.
4. Non-negotiable medical disclaimer inclusion.
5. Head-to-head comparison model output.
6. Database persistence of entry analysis metadata.
"""

import unittest
from app.db import get_db_connection, init_db
from app.repository import UserRepository, JournalRepository
from app.security import hash_password
from app.ai_analysis import (
    SIX_EMOTIONS,
    BiLSTMAugmentedAnalyzer,
    PretrainedRoBERTaAnalyzer,
    analyze_reflection,
    compute_uncertainty_notice
)
from ml.data_prep import map_label, GO_EMOTIONS_MAPPING


class TestMachineLearning(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection(":memory:")
        init_db(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.journal_repo = JournalRepository(self.conn)

        self.user_id = self.user_repo.create_user(
            username="analysistester",
            email="ml@example.com",
            password_hash=hash_password("Pass12345!")
        )

    def tearDown(self):
        self.conn.close()

    def test_goemotions_label_mapping_and_filtering(self):
        # Mapped positive
        self.assertEqual(map_label("grief"), "sadness")
        self.assertEqual(map_label("amusement"), "joy")
        self.assertEqual(map_label("admiration"), "love")
        self.assertEqual(map_label("annoyance"), "anger")
        self.assertEqual(map_label("nervousness"), "fear")
        self.assertEqual(map_label("curiosity"), "surprise")

        # Unmapped / filtered out (must return None to prevent noisy labels)
        self.assertIsNone(map_label("neutral"))
        self.assertIsNone(map_label("optimism"))
        self.assertIsNone(map_label("non_existent_label"))

    def test_input_truncation_at_4000_chars(self):
        analyzer = BiLSTMAugmentedAnalyzer()
        long_text = "word " * 1500  # ~7500 chars
        self.assertGreater(len(long_text), 4000)

        res = analyzer.analyze(long_text)
        self.assertLessEqual(res.char_count_analyzed, 4000)

    def test_bilstm_analysis_output_contract(self):
        text = "I felt immense joy, relief, and gratitude after completing our college capstone defense!"
        res = analyze_reflection(text)

        self.assertEqual(res.status, "completed")
        self.assertEqual(res.model_name, "EchoJournal-BiLSTM-Ekman6")
        self.assertIn(res.primary_emotion, SIX_EMOTIONS)
        self.assertEqual(res.primary_emotion, "joy")
        self.assertIn("joy", res.emotion_scores)
        self.assertAlmostEqual(sum(res.emotion_scores.values()), 1.0, places=2)
        self.assertEqual(res.sentiment_label, "positive")
        self.assertGreater(res.sentiment_score, 0.5)
        self.assertTrue(len(res.uncertainty_notice) > 0)
        self.assertIn("NOT a medical or diagnostic system", res.medical_disclaimer)

    def test_uncertainty_notice_generation(self):
        # Evenly spread / ambiguous scores
        flat_scores = {e: 0.166 for e in SIX_EMOTIONS}
        notice = compute_uncertainty_notice(flat_scores)
        self.assertIn("High Uncertainty", notice)

        # Clear dominant score
        dominant_scores = {"joy": 0.85, "sadness": 0.03, "love": 0.04, "anger": 0.02, "fear": 0.03, "surprise": 0.03}
        clear_notice = compute_uncertainty_notice(dominant_scores)
        self.assertIn("Distinct Trajectory", clear_notice)

    def test_roberta_comparison_output(self):
        text = "I am so anxious and scared about failing my algorithms exam."
        res = analyze_reflection(text, include_comparison=True)

        self.assertIsNotNone(res.comparison_model)
        self.assertIn("distilroberta", res.comparison_model["model_name"].lower())
        self.assertIn("explanatory_note", res.comparison_model)
        self.assertIn(res.comparison_model["primary_emotion"], SIX_EMOTIONS)

    def test_database_persistence_of_analysis(self):
        entry_id = self.journal_repo.create_entry(
            user_id=self.user_id,
            title="Graduation Joy",
            content="Celebrating with friends on campus. So grateful and proud."
        )

        res = analyze_reflection("Celebrating with friends on campus. So grateful and proud.")
        saved = self.journal_repo.save_entry_analysis(
            entry_id=entry_id,
            user_id=self.user_id,
            analysis_data=res.to_dict()
        )
        self.assertTrue(saved)

        # Fetch and verify stored fields
        entry = self.journal_repo.get_entry(entry_id, self.user_id)
        self.assertEqual(entry["analysis_status"], "completed")
        self.assertEqual(entry["primary_emotion"], res.primary_emotion)
        self.assertEqual(entry["model_name"], "EchoJournal-BiLSTM-Ekman6")
        self.assertIsNotNone(entry["analyzed_at"])


if __name__ == "__main__":
    unittest.main()
