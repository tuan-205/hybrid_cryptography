"""Giao diện dòng lệnh cho mô phỏng cục bộ."""
import argparse
import json
import os
from pathlib import Path
from . import crypto, session, storage
from .records import read_csv


def key(path, private=False):
    data = Path(path).read_bytes()
    return crypto.load_private(data) if private else crypto.load_public(data)


def write_key(path, data, private):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if private else 0o644)
    with os.fdopen(fd, "wb") as target:
        target.write(data)


def main():
    parser = argparse.ArgumentParser(description="Mo phong doi soat COD")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("keys", help="Tao cap khoa RSA cho ben phat hanh va shop")
    p.add_argument("directory")
    p = commands.add_parser("seal", help="Chot phien tu CSV")
    p.add_argument("csv"); p.add_argument("output")
    p.add_argument("--session", required=True); p.add_argument("--shop", required=True)
    p.add_argument("--issuer-private", required=True); p.add_argument("--issuer-public", required=True)
    p.add_argument("--shop-public", required=True); p.add_argument("--previous")
    p = commands.add_parser("open", help="Giai ma va kiem tra phien")
    p.add_argument("package"); p.add_argument("--shop-private", required=True)
    p.add_argument("--issuer-public", required=True); p.add_argument("--previous")
    args = parser.parse_args()
    try:
        if args.command == "keys":
            directory = Path(args.directory)
            directory.mkdir(parents=True, exist_ok=True)
            paths = [directory / (name + suffix) for name in ("issuer", "shop") for suffix in ("_private.pem", "_public.pem")]
            if any(p.exists() for p in paths):
                raise ValueError("File khoa da ton tai; chon thu muc moi")
            for name in ("issuer", "shop"):
                private, public = crypto.generate_keypair()
                write_key(directory / (name + "_private.pem"), private, True)
                write_key(directory / (name + "_public.pem"), public, False)
            print("Da tao khoa trong", directory)
        elif args.command == "seal":
            private = key(args.issuer_private, True)
            public = key(args.issuer_public)
            # Ensure the signing key matches the public key used to verify history.
            crypto.verify(b"key-check", crypto.sign(b"key-check", private), public)
            previous = storage.read_json(args.previous) if args.previous else None
            package = session.seal(read_csv(args.csv), args.session, args.shop, key(args.shop_public), private, previous, public)
            storage.write_json(args.output, package)
            print("Da chot phien ban", package["metadata"]["version"], "tai", args.output)
        else:
            previous = storage.read_json(args.previous) if args.previous else None
            result = session.open_session(storage.read_json(args.package), key(args.shop_private, True), key(args.issuer_public), previous)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if not all(result["valid"]):
                return 1
    except Exception as exc:
        print("Loi:", str(exc) or type(exc).__name__, file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
