"""Chạy: python experiments/tamper_demo.py"""
from pathlib import Path
import copy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid_crypto import crypto, session
from hybrid_crypto.records import read_csv, validate


def main():
    root = Path(__file__).resolve().parents[1]
    records = read_csv(root / "data/input/sample_cod.csv")
    issuer_private, issuer_public = map(lambda pair: pair, crypto.generate_keypair())
    shop_private, shop_public = crypto.generate_keypair()
    issuer_private, issuer_public = crypto.load_private(issuer_private), crypto.load_public(issuer_public)
    shop_private, shop_public = crypto.load_private(shop_private), crypto.load_public(shop_public)
    package = session.seal(records, "DS001", "SHOP001", shop_public, issuer_private)
    opened = session.open_session(package, shop_private, issuer_public)
    assert all(opened["valid"]), "Phien goc khong hop le"
    changed = copy.deepcopy(opened["records"])
    changed[0]["shipping_fee"], changed[0]["shop_amount"] = 75000, 225000
    validate(changed)
    matches = session.verify_record(changed[0], opened["metadata"], 0, package["records"][0]["proof"])
    print("Phien goc:", "khop" if all(opened["valid"]) else "khong khop")
    print("VD001 sau sua: phep tinh dung; Merkle", "khop" if matches else "khong khop")
    assert not matches, "Khong phat hien thay doi"
    new = session.seal(changed, "DS001", "SHOP001", shop_public, issuer_private, package, issuer_public)
    verified = session.open_session(new, shop_private, issuer_public, package)
    assert all(verified["valid"]) and verified["chain"] == "khop"
    print("Phien ban moi:", new["metadata"]["version"], "- lien ket phien truoc khop")


if __name__ == "__main__":
    main()
