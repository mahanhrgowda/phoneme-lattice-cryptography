import unittest
import plc_core
import devanagari
import panini
import sandhi
import bhava_vectors
import trishula_lab
import panini_engine

class TestRoundTrip(unittest.TestCase):
    def test_examples(self):
        for value in ["maheshwara", "kṣetraṃ", "ātmā", "Mahan, नमः!", "ai au ṛ"]:
            self.assertEqual(plc_core.decode(plc_core.encode(value)), value)
    def test_devanagari_transliteration(self):
        self.assertEqual(devanagari.transliterate("नमः शिवाय"), "namaḥ śivāya")
        self.assertEqual(devanagari.transliterate("राम"), "rāma")
    def test_pratyahara_ac(self):
        self.assertEqual(panini.pratyahara("a", "c"), ["a","i","u","ṛ","ḷ","e","o","ai","au"])
    def test_pratyahara_hal(self):
        self.assertIn("k", panini.pratyahara("h", "l", 0, 0))
    def test_codebook_unique(self):
        report = plc_core.validate_codebook()
        self.assertTrue(report["reversible"])
        self.assertEqual(report["token_count"], report["unique_coordinate_count"])
    def test_sandhi_rule(self):
        self.assertEqual(sandhi.apply("a", "i")[0]["result"], "e")
    def test_bhava_vector_validation(self):
        row = bhava_vectors.vector("Rāgaḥ", "Anāhata", "Śṛṅgāra", 0.7, "ma")
        self.assertEqual(row["phoneme"], "ma")
        with self.assertRaises(ValueError):
            bhava_vectors.vector("not-a-bhava")
    def test_trishula_round_trip(self):
        records = plc_core.encode("maha")["records"]
        changed = trishula_lab.transform(records, (1,2,3), 17)
        restored = trishula_lab.reverse(changed, (1,2,3), 17)
        self.assertEqual(restored, records)
    def test_panini_guna_boundary(self):
        matches = panini_engine.apply_boundary("deva", "indra")
        self.assertTrue(any(m["result"] == "devendra" and m["sutra"] == "6.1.87" for m in matches))
    def test_panini_yan_boundary(self):
        matches = panini_engine.apply_boundary("iti", "atra")
        self.assertTrue(any(m["result"] == "ityatra" and m["sutra"] == "6.1.77" for m in matches))
    def test_coordinate_spec_separates_semantic_axes(self):
        spec = panini_engine.explain_coordinate_profile()
        self.assertEqual(spec["separate_conceptual_axes"]["X"], "Bhūta")
        self.assertEqual(len(spec["dimensions"]), 6)
    def test_tampering_rejected(self):
        payload = plc_core.encode("namaste")
        payload["records"][0]["coordinate"][0] += 1
        with self.assertRaises(ValueError):
            plc_core.decode(payload)

if __name__ == "__main__":
    unittest.main()
