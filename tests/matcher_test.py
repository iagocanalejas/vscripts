import unittest

from vscripts.matcher import NameMatcher


class TestNameMatcher(unittest.TestCase):
    def test_matches_season_x_episode(self):
        matcher = NameMatcher("Los Simpson - 2x04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertTrue(matcher.matches_season_x_episode())

    def test_matches_s_season_e_episode(self):
        matcher = NameMatcher("Los Simpson - S2E04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertTrue(matcher.matches_s_season_e_episode())

    def test_matches_cap_dot_season_episode(self):
        matcher = NameMatcher("Los Simpson - Temporada 6 [DVDRIP][cap.601][Spanish][www.pctestrenos.com].avi")
        self.assertTrue(matcher.matches_cap_dot_season_episode())

    def test_clean_season_x_episode(self):
        matcher = NameMatcher("Los Simpson - 2x04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertEqual(
            "Los Simpson - S2E04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.mkv",
            matcher.clean_season_x_episode(),
        )

    def test_clean_s_season_e_episode(self):
        matcher = NameMatcher("Los Simpson - S2E04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertEqual(
            "Los Simpson - S2E04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.mkv",
            matcher.clean_s_season_e_episode(),
        )

    def test_clean_cap_dot_season_episode(self):
        matcher = NameMatcher("Los Simpson - Temporada 6 [DVDRIP][cap.601][Spanish][www.pctestrenos.com].avi")
        self.assertEqual("Los Simpson - S06E01.mkv", matcher.clean_cap_dot_season_episode())
