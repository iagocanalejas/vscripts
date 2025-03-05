import unittest

from vscripts.matcher import NameMatcher


class TestNameMatcher(unittest.TestCase):
    def test_classify(self):
        matcher = NameMatcher("Los Simpson - 2x04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertEqual(NameMatcher.Type.X_NAME, matcher.classify())

        matcher = NameMatcher("Los Simpson - S2E04 - Dos Coches En Cada Garaje Y Tres Ojos En Cada Pez.avi")
        self.assertEqual(NameMatcher.Type.SE_NAME, matcher.classify())

        matcher = NameMatcher("Los Simpson - Temporada 6 [DVDRIP][cap.601][Spanish][www.pctestrenos.com].avi")
        self.assertEqual(NameMatcher.Type.CAP_DOT_NAME, matcher.classify())

    def test_clean(self):
        matcher = NameMatcher("Los Simpson - 2x04 - Dos Coches En Cada.avi")
        self.assertEqual("Los Simpson - S02E04 - Dos Coches En Cada.mkv", matcher.clean())

        matcher = NameMatcher("9x07 - Las dos señoras Nahasapeemapetilon.avi")
        self.assertEqual("S09E07 - Las dos señoras Nahasapeemapetilon.mkv", matcher.clean())

        matcher = NameMatcher("Los Simpson - S2E04 - Dos Coches En Cada.avi")
        self.assertEqual("Los Simpson - S02E04 - Dos Coches En Cada.mkv", matcher.clean())

        matcher = NameMatcher("Los Simpson - Temporada 6 [DVDRIP][cap.601][Spanish][www.pctestrenos.com].avi")
        self.assertEqual("Los Simpson - S06E01.mkv", matcher.clean())
