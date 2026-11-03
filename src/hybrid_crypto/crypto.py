"""Các phép mật mã dùng thư viện cryptography."""
import base64
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def b64(data):
    return base64.b64encode(data).decode("ascii")


def unb64(value):
    return base64.b64decode(value, validate=True)


def generate_keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return (private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
            private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))


def load_private(data):
    return serialization.load_pem_private_key(data, password=None)


def load_public(data):
    return serialization.load_pem_public_key(data)


def oaep():
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


def encrypt(data, public_key, aad):
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    return {"nonce": b64(nonce), "ciphertext": b64(AESGCM(key).encrypt(nonce, data, aad)), "wrapped_key": b64(public_key.encrypt(key, oaep()))}


def decrypt(item, private_key, aad):
    key = private_key.decrypt(unb64(item["wrapped_key"]), oaep())
    return AESGCM(key).decrypt(unb64(item["nonce"]), unb64(item["ciphertext"]), aad)


def sign(data, private_key):
    return b64(private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256()))


def verify(data, signature, public_key):
    public_key.verify(unb64(signature), data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
