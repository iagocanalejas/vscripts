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

        matcher = NameMatcher("Los.Simpsons.T07.Cap.01.Quien.Disparo.al.Sr.Burns.Parte.II..mkv")
        self.assertEqual(NameMatcher.Type.T_CAP_NAME, matcher.classify())

        matcher = NameMatcher("A.Mascara.-.01.DVBRip.Galego.por.BlueLynx.[www.OsArquivosDaMeiga.co.nr].avi")
        self.assertEqual(NameMatcher.Type.CAP, matcher.classify())

        matcher = NameMatcher("Wolverine_e_os_X-Men-01-Retrospectiva-Parte_I-BDRip-720p-[Sub]-[Galego-English].mkv")
        self.assertEqual(NameMatcher.Type.CAP, matcher.classify())

    def test_clean(self):
        matcher = NameMatcher("Los Simpson - 2x04 - Dos Coches En Cada.avi")
        self.assertEqual("Los Simpson - S02E04 - Dos Coches En Cada.mkv", matcher.clean())

        matcher = NameMatcher("Como_Conoci_A_Vuestra_Madre_1x19_Mary,_La_Asistente_Legal_Webdl_M-1080pDUAL.mkv")
        self.assertEqual("Como Conoci A Vuestra Madre - S01E19 - Mary, La Asistente Legal.mkv", matcher.clean())

        matcher = NameMatcher("9x07 - Las dos señoras Nahasapeemapetilon.avi")
        self.assertEqual("S09E07 - Las dos señoras Nahasapeemapetilon.mkv", matcher.clean())

        matcher = NameMatcher("Los Simpson - S2E04 - Dos Coches En Cada.avi")
        self.assertEqual("Los Simpson - S02E04 - Dos Coches En Cada.mkv", matcher.clean())

        matcher = NameMatcher("Los Simpson - Temporada 6 [DVDRIP][cap.601][Spanish][www.pctestrenos.com].avi")
        self.assertEqual("Los Simpson - S06E01.mkv", matcher.clean())

        matcher = NameMatcher("Los Simpsons - Temporada 29 [HDTV 720p][Cap.2904][AC3 5.1 Castellano][www.PctMix.Com]")
        self.assertEqual("Los Simpsons - S29E04.mkv", matcher.clean())

        matcher = NameMatcher("Los.Simpsons.T07.Cap.01.Quien.Disparo.al.Sr.Burns.Parte.II..mkv")
        self.assertEqual("Los Simpsons - S07E01 - Quien Disparo al Sr Burns Parte II.mkv", matcher.clean())

        matcher = NameMatcher("A.Mascara.-.01.DVBRip.Galego.por.BlueLynx.[www.OsArquivosDaMeiga.co.nr].avi")
        self.assertEqual("A Mascara - 01.mkv", matcher.clean())

        matcher = NameMatcher("Wolverine_e_os_X-Men-01-Retrospectiva-Parte_I-BDRip-720p-[Sub]-[Galego-English].mkv")
        self.assertEqual("Wolverine e os X - Men - 01 - Retrospectiva - Parte I.mkv", matcher.clean())
