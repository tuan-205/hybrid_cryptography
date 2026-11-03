import copy
import sys
import unittest
from pathlib import Path
from cryptography.exceptions import InvalidSignature

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid_crypto import crypto, integrity, session
from hybrid_crypto.records import read_csv, validate


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        priv, pub = crypto.generate_keypair()
        cls.issuer_private, cls.issuer_public = crypto.load_private(priv), crypto.load_public(pub)
        priv, pub = crypto.generate_keypair()
        cls.shop_private, cls.shop_public = crypto.load_private(priv), crypto.load_public(pub)
        cls.records = read_csv(Path(__file__).resolve().parents[1] / "data/input/sample_cod.csv")

    def seal(self, records=None, previous=None):
        return session.seal(records or self.records, "DS001", "SHOP001", self.shop_public, self.issuer_private, previous, self.issuer_public)

    def test_roundtrip_tamper_and_new_version(self):
        original = self.seal()
        opened = session.open_session(original, self.shop_private, self.issuer_public)
        self.assertEqual(opened["records"], self.records)
        self.assertEqual(opened["valid"], [True, True])
        changed = copy.deepcopy(self.records)
        changed[0].update(shipping_fee=75000, shop_amount=225000)
        validate(changed)
        self.assertFalse(session.verify_record(changed[0], opened["metadata"], 0, original["records"][0]["proof"]))
        newer = self.seal(changed, original)
        result = session.open_session(newer, self.shop_private, self.issuer_public, original)
        self.assertEqual(result["chain"], "khop")
        self.assertEqual(result["records"], changed)
        self.assertEqual(session.open_session(original, self.shop_private, self.issuer_public)["records"], self.records)
        with self.assertRaises(ValueError):
            session.open_session(newer, self.shop_private, self.issuer_public, newer)

    def test_tampering(self):
        original = self.seal()
        forged = copy.deepcopy(original)
        forged["metadata"]["merkle_root"] = "0" * 64
        with self.assertRaises(InvalidSignature):
            session.open_session(forged, self.shop_private, self.issuer_public)
        forged = copy.deepcopy(original)
        raw = bytearray(crypto.unb64(forged["records"][0]["ciphertext"]))
        raw[0] ^= 1
        forged["records"][0]["ciphertext"] = crypto.b64(raw)
        self.assertEqual(session.open_session(forged, self.shop_private, self.issuer_public)["valid"], [False, True])
        forged = copy.deepcopy(original)
        forged["records"][0]["proof"][0]["hash"] = "00" * 32
        self.assertEqual(session.open_session(forged, self.shop_private, self.issuer_public)["valid"], [False, True])

    def test_validation_and_proofs(self):
        with self.assertRaises(ValueError):
            validate(self.records + self.records)
        with self.assertRaises(ValueError):
            validate([dict(self.records[0], shop_amount=123)])
        data = [b"a", b"b", b"c"]
        root, proofs = integrity.merkle(data)
        for i in range(3):
            self.assertTrue(integrity.verify_proof(data[i], i, 3, proofs[i], root))
            self.assertFalse(integrity.verify_proof(b"other", i, 3, proofs[i], root))
        self.assertFalse(integrity.verify_proof(data[0], 0, 3, [], root))


if __name__ == "__main__":
    unittest.main()
