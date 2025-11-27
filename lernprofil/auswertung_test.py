#!/usr/bin/env python3
"""
Unit-Tests für scoring_v02.py

Testet die Kernfunktionalität des Auswertungssystems:
- Reverse-Coding
- Score-Berechnung
- Chronotyp-Index
- Response-Quality-Checks
- Extremprofile
"""

import unittest
import sys
from pathlib import Path

# Scoring-Modul importieren
sys.path.insert(0, str(Path(__file__).parent))
import auswertung as scoring


class TestScoringBasics(unittest.TestCase):
    """Tests für grundlegende Scoring-Funktionen."""
    
    def test_reverse_likert_mapping(self):
        """Teste Reverse-Coding: 1<->5, 2<->4, 3->3."""
        self.assertEqual(scoring.reverse_likert(1), 5)
        self.assertEqual(scoring.reverse_likert(2), 4)
        self.assertEqual(scoring.reverse_likert(3), 3)
        self.assertEqual(scoring.reverse_likert(4), 2)
        self.assertEqual(scoring.reverse_likert(5), 1)
        
        with self.assertRaises(ValueError):
            scoring.reverse_likert(0)
        with self.assertRaises(ValueError):
            scoring.reverse_likert(6)
    
    def test_classify_score_thresholds(self):
        """Teste Kategorisierungs-Schwellenwerte."""
        self.assertEqual(scoring.classify_score(0.0), "niedrig")
        self.assertEqual(scoring.classify_score(39.9), "niedrig")
        self.assertEqual(scoring.classify_score(40.0), "mittel")
        self.assertEqual(scoring.classify_score(74.9), "mittel")
        self.assertEqual(scoring.classify_score(75.0), "hoch")
        self.assertEqual(scoring.classify_score(100.0), "hoch")


class TestExtremProfiles(unittest.TestCase):
    """Tests für Extremprofile (alle niedrig/hoch)."""
    
    def _make_ratings_for_extreme_profile(self, high: bool) -> dict:
        """
        Erzeugt ein Rating-Dict für Extremprofile.
        Nach Reverse-Coding sollten alle Werte entweder minimal oder maximal sein.
        """
        ratings = {}
        for code, item_def in scoring.ITEM_DEFINITIONS.items():
            if high:
                # Nach Reverse-Coding soll hoher Wert entstehen
                if item_def.reverse_scored:
                    ratings[code] = scoring.LIKERT_MIN  # -> max nach Reverse
                else:
                    ratings[code] = scoring.LIKERT_MAX
            else:
                # Nach Reverse-Coding soll niedriger Wert entstehen
                if item_def.reverse_scored:
                    ratings[code] = scoring.LIKERT_MAX  # -> min nach Reverse
                else:
                    ratings[code] = scoring.LIKERT_MIN
        return ratings
    
    def test_all_low_scores_result_in_zero(self):
        """Teste, dass alle minimalen Antworten Score von 0 ergeben."""
        ratings = self._make_ratings_for_extreme_profile(high=False)
        profile = scoring.compute_profile(ratings, profile_id="low_profile")
        
        for dim_code, dim in profile["dimensions"].items():
            self.assertAlmostEqual(0.0, dim["score"], places=1, 
                                 msg=f"Dimension {dim_code} nicht bei 0")
    
    def test_all_high_scores_result_in_hundred(self):
        """Teste, dass alle maximalen Antworten Score von 100 ergeben."""
        ratings = self._make_ratings_for_extreme_profile(high=True)
        profile = scoring.compute_profile(ratings, profile_id="high_profile")
        
        for dim_code, dim in profile["dimensions"].items():
            self.assertAlmostEqual(100.0, dim["score"], places=1,
                                 msg=f"Dimension {dim_code} nicht bei 100")


class TestChronotype(unittest.TestCase):
    """Tests für Chronotyp-Berechnung."""
    
    def test_clear_morning_type(self):
        """Teste eindeutigen Morgentyp."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        # Morgen-Items hoch, Abend-Items niedrig
        for code in ["A8", "A13", "A14", "A15"]:
            ratings[code] = 5
        for code in ["A9", "A16"]:
            ratings[code] = 1
        
        chronotype = scoring.compute_chronotype_index(ratings)
        self.assertLess(chronotype["balance_score"], -0.8)
        self.assertIn("Morgentyp", chronotype["interpretation"])
    
    def test_clear_evening_type(self):
        """Teste eindeutigen Abendtyp."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        # Morgen-Items niedrig, Abend-Items hoch
        for code in ["A8", "A13", "A14", "A15"]:
            ratings[code] = 1
        for code in ["A9", "A16"]:
            ratings[code] = 5
        
        chronotype = scoring.compute_chronotype_index(ratings)
        self.assertGreater(chronotype["balance_score"], 0.8)
        self.assertIn("Abendtyp", chronotype["interpretation"])
    
    def test_neutral_chronotype(self):
        """Teste neutralen Chronotyp."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        
        chronotype = scoring.compute_chronotype_index(ratings)
        self.assertAlmostEqual(chronotype["balance_score"], 0.0, delta=0.1)
        self.assertIn("Neutral", chronotype["interpretation"])


class TestResponseQuality(unittest.TestCase):
    """Tests für Response-Quality-Checks."""
    
    def test_straight_lining_detection(self):
        """Teste Erkennung von Straight-Lining (nur eine Antwort)."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        quality = scoring.check_response_quality(ratings)
        
        self.assertEqual(quality["num_unique_responses"], 1)
        self.assertEqual(quality["quality_flag"], "check")
        self.assertIn(scoring.QUALITY_WARN_STRAIGHT, quality["warnings"])
    
    def test_normal_response_pattern(self):
        """Teste normales Antwortmuster."""
        ratings = {}
        for i, code in enumerate(scoring.ITEM_DEFINITIONS.keys()):
            ratings[code] = (i % 5) + 1  # Werte 1-5 rotierend
        
        quality = scoring.check_response_quality(ratings)
        
        self.assertEqual(quality["num_unique_responses"], 5)
        self.assertEqual(quality["quality_flag"], "ok")
        self.assertIsNone(quality["warnings"])


class TestDimensionalIndependence(unittest.TestCase):
    """Tests für dimensionale Unabhängigkeit."""
    
    def test_manipulation_only_affects_target_dimension(self):
        """
        Teste, dass Änderungen in einer Dimension andere nicht beeinflussen.
        """
        # Basis-Profil mit neutralen Werten
        base_ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        
        # Setze nur Aufmerksamkeits-Items auf Maximum
        for code, item_def in scoring.ITEM_DEFINITIONS.items():
            if item_def.dimension_code == "attention" and item_def.include_in_main_scale:
                base_ratings[code] = 5 if not item_def.reverse_scored else 1
        
        profile = scoring.compute_profile(base_ratings)
        
        # Aufmerksamkeit sollte hoch sein
        self.assertGreater(profile["dimensions"]["attention"]["score"], 90)
        
        # Andere Dimensionen sollten bei ~50 bleiben (3 auf Likert → 50 auf 0-100)
        for dim in ["sensory", "social", "executive", "motivation", "regulation"]:
            score = profile["dimensions"][dim]["score"]
            self.assertAlmostEqual(score, 50.0, delta=10.0,
                                 msg=f"Dimension {dim} sollte neutral bleiben, ist aber {score}")


class TestRatingValidation(unittest.TestCase):
    """Tests für validate_ratings Funktion."""
    
    def test_missing_items_raises(self):
        """Teste, dass fehlende Items einen ValueError werfen."""
        ratings = {code: 3 for code in list(scoring.ITEM_DEFINITIONS.keys())[:-1]}
        with self.assertRaises(ValueError) as ctx:
            scoring.validate_ratings(ratings)
        self.assertIn("Fehlende Items", str(ctx.exception))

    def test_extra_items_raises(self):
        """Teste, dass extra Items einen ValueError werfen."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        ratings["XXX"] = 3
        with self.assertRaises(ValueError) as ctx:
            scoring.validate_ratings(ratings)
        self.assertIn("Unbekannte Items", str(ctx.exception))

    def test_invalid_type_raises(self):
        """Teste, dass nicht-int Werte einen TypeError werfen."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        some_code = next(iter(ratings))
        ratings[some_code] = "3"
        with self.assertRaises(TypeError) as ctx:
            scoring.validate_ratings(ratings)
        self.assertIn("kein int", str(ctx.exception))
    
    def test_out_of_range_raises(self):
        """Teste, dass Werte außerhalb 1-5 einen ValueError werfen."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        some_code = next(iter(ratings))
        ratings[some_code] = 6
        with self.assertRaises(ValueError) as ctx:
            scoring.validate_ratings(ratings)
        self.assertIn("außerhalb des erlaubten Bereichs", str(ctx.exception))
    
    def test_valid_ratings_pass(self):
        """Teste, dass valide Ratings keine Exception werfen."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        try:
            scoring.validate_ratings(ratings)
        except Exception as e:
            self.fail(f"validate_ratings sollte nicht fehlschlagen bei validen Ratings: {e}")


class TestItemCounts(unittest.TestCase):
    """Tests für dimensionale Unabhängigkeit."""
    
    def test_manipulation_only_affects_target_dimension(self):
        """
        Teste, dass Änderungen in einer Dimension andere nicht beeinflussen.
        """
        # Basis-Profil mit neutralen Werten
        base_ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        
        # Setze nur Aufmerksamkeits-Items auf Maximum
        for code, item_def in scoring.ITEM_DEFINITIONS.items():
            if item_def.dimension_code == "attention" and item_def.include_in_main_scale:
                base_ratings[code] = 5 if not item_def.reverse_scored else 1
        
        profile = scoring.compute_profile(base_ratings)
        
        # Aufmerksamkeit sollte hoch sein
        self.assertGreater(profile["dimensions"]["attention"]["score"], 90)
        
        # Andere Dimensionen sollten bei ~50 bleiben (3 auf Likert → 50 auf 0-100)
        for dim in ["sensory", "social", "executive", "motivation", "regulation"]:
            score = profile["dimensions"][dim]["score"]
            self.assertAlmostEqual(score, 50.0, delta=10.0,
                                 msg=f"Dimension {dim} sollte neutral bleiben, ist aber {score}")


class TestItemCounts(unittest.TestCase):
    """Tests für korrekte Item-Zählungen."""
    
    def test_total_item_count(self):
        """Teste Gesamt-Itemzahl: 88 Items."""
        self.assertEqual(len(scoring.ITEM_DEFINITIONS), 88)
    
    def test_main_scale_items(self):
        """Teste Haupt-Skalen-Items: 80 Items."""
        main_items = [item for item in scoring.ITEM_DEFINITIONS.values() 
                     if item.include_in_main_scale]
        self.assertEqual(len(main_items), 80)
    
    def test_separate_index_items(self):
        """Teste separate Index-Items: 8 Items."""
        separate_items = [item for item in scoring.ITEM_DEFINITIONS.values() 
                         if not item.include_in_main_scale]
        self.assertEqual(len(separate_items), 8)
    
    def test_reverse_item_count(self):
        """Teste Reverse-Items in Hauptskalen: 27 Items."""
        reverse_main = [item for item in scoring.ITEM_DEFINITIONS.values() 
                       if item.include_in_main_scale and item.reverse_scored]
        self.assertEqual(len(reverse_main), 27)
    
    def test_motivation_has_reverse_items(self):
        """Teste, dass Motivation mindestens 4 Reverse-Items hat (Fix von v0.1)."""
        motivation_reverse = [item for item in scoring.ITEM_DEFINITIONS.values() 
                             if item.dimension_code == "motivation" 
                             and item.include_in_main_scale 
                             and item.reverse_scored]
        self.assertGreaterEqual(len(motivation_reverse), 4,
                               "Motivation sollte mindestens 4 Reverse-Items haben")


class TestMetadataConsistency(unittest.TestCase):
    """Tests für Konsistenz der Metadaten."""
    
    def test_profile_metadata_accurate(self):
        """Teste, dass Profil-Metadaten korrekt sind."""
        ratings = {code: 3 for code in scoring.ITEM_DEFINITIONS.keys()}
        profile = scoring.compute_profile(ratings)
        
        meta = profile["meta"]
        self.assertEqual(meta["version"], "0.2.1")
        self.assertEqual(meta["num_items_instrument"], 88)
        self.assertEqual(meta["num_items_answered"], 88)
        self.assertEqual(meta["num_items_main_scales"], 80)
        self.assertEqual(meta["num_items_additional"], 8)
        self.assertEqual(meta["num_reversed_total"], 27)


def run_tests():
    """Führe alle Tests aus und gebe Zusammenfassung aus."""
    # Test-Suite erstellen
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Alle Test-Klassen hinzufügen
    suite.addTests(loader.loadTestsFromTestCase(TestScoringBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestExtremProfiles))
    suite.addTests(loader.loadTestsFromTestCase(TestChronotype))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionalIndependence))
    suite.addTests(loader.loadTestsFromTestCase(TestRatingValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestItemCounts))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadataConsistency))
    
    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("TEST-ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"Tests durchgeführt: {result.testsRun}")
    print(f"Erfolgreich: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fehlgeschlagen: {len(result.failures)}")
    print(f"Fehler: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
