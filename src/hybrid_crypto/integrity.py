"""SHA-256, Merkle proof và hash của phiên đã ký."""
import hashlib
from .records import canonical


def digest(data):
    return hashlib.sha256(data).digest()


def leaf(data):
    return digest(b"\x00" + data)


def parent(left, right):
    return digest(b"\x01" + left + right)

# xay dung cay merkle
def merkle(data):
    if not data:
        raise ValueError("Khong the tao cay Merkle rong")
    levels = [[leaf(item) for item in data]]
    while len(levels[-1]) > 1:
        level = levels[-1]
        levels.append([parent(level[i], level[i + 1] if i + 1 < len(level) else level[i]) for i in range(0, len(level), 2)])
    proofs = []
    for index in range(len(data)):
        pos = index
        proof = []
        for level in levels[:-1]:
            sibling = pos ^ 1
            proof.append({"side": "left" if pos % 2 else "right", "hash": (level[sibling] if sibling < len(level) else level[pos]).hex()})
            pos //= 2
        proofs.append(proof)
    # luu lai level + bang chung cho record
    return levels[-1][0].hex(), proofs

# xac thuc bang chung
def verify_proof(data, index, count, proof, root):
    if type(index) is not int or type(count) is not int or count < 1 or not 0 <= index < count or not isinstance(proof, list):
        return False
    try:
        current = leaf(data)
        pos, width = index, count
        # tinh lai step tu record -> root
        for step in proof:
            if width <= 1 or set(step) != {"side", "hash"} or step["side"] != ("left" if pos % 2 else "right"):
                return False
            sibling = bytes.fromhex(step["hash"])
            # phat hien noi dung khong con khop voi du lieu da chot
            if len(sibling) != 32 or (pos % 2 == 0 and pos + 1 >= width and sibling != current):
                return False
            current = parent(sibling, current) if pos % 2 else parent(current, sibling)
            pos //= 2
            width = (width + 1) // 2
        return width == 1 and current.hex() == root
    except (ValueError, TypeError, KeyError):
        return False

# tao gia tri bam ngan gon va khong the dao nguoc
def session_hash(package):
    return digest(canonical({"metadata": package["metadata"], "signature": package["signature"]})).hex()
