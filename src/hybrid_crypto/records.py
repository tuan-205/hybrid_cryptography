"""Đọc, kiểm tra và chuẩn hóa bản ghi COD."""
import csv
import json

FIELDS = ("tracking_id", "cod", "shipping_fee", "shop_amount")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def validate(records):
    if not records:
        raise ValueError("Danh sach ban ghi rong")
    seen = set()
    for record in records:
        if set(record) != set(FIELDS):
            raise ValueError("Ban ghi phai co dung cac truong CSV")
        tracking = record["tracking_id"]
        if not isinstance(tracking, str) or not tracking or tracking != tracking.strip() or tracking in seen:
            raise ValueError("Ma van don rong, co khoang trang thua hoac bi trung")
        seen.add(tracking)
        for field in FIELDS[1:]:
            if type(record[field]) is not int or record[field] < 0:
                raise ValueError(f"{field} phai la so nguyen khong am")
        if record["cod"] - record["shipping_fee"] != record["shop_amount"]:
            raise ValueError(f"Phep tinh khong dung: {tracking}")
    return records


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Cot CSV phai theo thu tu: " + ",".join(FIELDS))
        records = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Dong CSV thieu hoac thua cot")
            for field in FIELDS[1:]:
                if not row[field].isascii() or not row[field].isdigit():
                    raise ValueError(f"{field} phai la so nguyen dong")
                row[field] = int(row[field])
            records.append(row)
    return validate(records)


def record_bytes(record, metadata, index):
    return canonical({"record": record, "session_id": metadata["session_id"], "shop_id": metadata["shop_id"], "version": metadata["version"], "index": index})
