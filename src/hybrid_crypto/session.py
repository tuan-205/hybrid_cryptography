"""Chốt, mở và xác minh phiên đối soát."""
import json
from cryptography.exceptions import InvalidSignature, InvalidTag
from . import crypto, integrity
from .records import canonical, record_bytes, validate


def authenticated_metadata(package, issuer_public):
    if package.get("format") != "cod-session-v1":
        raise ValueError("Dinh dang goi khong ho tro")
    meta = package["metadata"]
    # xac minh chu ky so
    crypto.verify(canonical(meta), package["signature"], issuer_public)
    if (set(meta) != {"session_id", "shop_id", "version", "previous_hash", "record_count", "merkle_root"}
            or not isinstance(meta["session_id"], str) or not meta["session_id"].strip()
            or not isinstance(meta["shop_id"], str) or not meta["shop_id"].strip()
            or type(meta["version"]) is not int or meta["version"] < 1
            or type(meta["record_count"]) is not int or meta["record_count"] < 1
            or not isinstance(meta["merkle_root"], str) or len(meta["merkle_root"]) != 64):
        raise ValueError("Thong tin phien khong hop le")
    if meta["version"] == 1:
        if meta["previous_hash"] is not None:
            raise ValueError("Phien ban dau khong co hash truoc")
    elif not isinstance(meta["previous_hash"], str) or len(meta["previous_hash"]) != 64:
        raise ValueError("Thieu hash phien truoc")
    return meta

# dieu phoi mo hinh
def seal(records, session_id, shop_id, shop_public, issuer_private, previous=None, issuer_public=None):
    validate(records)
    if not isinstance(session_id, str) or not session_id.strip() or not isinstance(shop_id, str) or not shop_id.strip():
        raise ValueError("Ma phien va ma shop khong duoc rong")
    # luu gia tri bam cua session truoc vao session moi 
    version, previous_hash = 1, None
    if previous is not None:
        if issuer_public is None:
            raise ValueError("Can khoa cong khai ben phat hanh")
        old = authenticated_metadata(previous, issuer_public)
        if (old["session_id"], old["shop_id"]) != (session_id, shop_id):
            raise ValueError("Phien truoc khong cung ma phien va shop")
        version, previous_hash = old["version"] + 1, integrity.session_hash(previous)
    # ky metadata
    meta = {"session_id": session_id, 
            "shop_id": shop_id, 
            "version": version, 
            "previous_hash": previous_hash, 
            "record_count": len(records)}
    inputs = [record_bytes(record, meta, i) for i, record in enumerate(records)]
    # xay cay merkle
    root, proofs = integrity.merkle(inputs)
    meta["merkle_root"] = root
    # ma hoa tung ban ghi
    encrypted = [crypto.encrypt(canonical(record), shop_public, record_bytes_context(meta, i)) for i, record in enumerate(records)]
    # ky thong tin session
    return {"format": "cod-session-v1", 
            "metadata": meta, 
            "signature": crypto.sign(canonical(meta), issuer_private), 
            "records": [{**item, "proof": proof} for item, proof in zip(encrypted, proofs)]}


def record_bytes_context(meta, index):
    return canonical({"session_id": meta["session_id"], "shop_id": meta["shop_id"], "version": meta["version"], "index": index})


def verify_record(record, meta, index, proof):
    return integrity.verify_proof(record_bytes(record, meta, index), index, meta["record_count"], proof, meta["merkle_root"])

# quy trinh nhan va xac thuc
def open_session(package, shop_private, issuer_public, previous=None):
    meta = authenticated_metadata(package, issuer_public)
    chain = "khong co phien truoc" if meta["version"] == 1 else "chua doi chieu phien truoc"
    # kiem tra neu co session truoc do
    if previous is not None:
        old = authenticated_metadata(previous, issuer_public)
        if (meta["version"] != old["version"] + 1 or meta["previous_hash"] != integrity.session_hash(previous)
                or meta["session_id"] != old["session_id"] or meta["shop_id"] != old["shop_id"]):
            raise ValueError("Lien ket phien truoc khong khop")
        chain = "khop"
    items = package["records"]
    if not isinstance(items, list) or len(items) != meta["record_count"]:
        raise ValueError("So luong ban ghi khong khop")
    records, checks = [], []
    for index, item in enumerate(items):
        try:
            # giai ma ban ghi
            record = json.loads(crypto.decrypt(item, shop_private, record_bytes_context(meta, index)))
            # kiem tra ban ghi kem theo proof
            ok = verify_record(record, meta, index, item["proof"])
        except (InvalidTag, ValueError, KeyError, TypeError, UnicodeError):
            record, ok = None, False
        records.append(record)
        checks.append(ok)
    if all(checks):
        try:
            validate(records)
        except (ValueError, TypeError):
            checks = [False] * len(checks)
    return {"metadata": meta, "records": records, "valid": checks, "chain": chain}
