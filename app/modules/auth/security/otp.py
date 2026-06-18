import hashlib
import secrets


def generate_otp() -> str:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    return otp


def hash_otp(otp: str) -> str:
    return hashlib.sha512(otp.encode("utf-8")).hexdigest()


def verify_otp(computed_otp_hash: str, stored_otp_hash: str) -> bool:
    return secrets.compare_digest(computed_otp_hash, stored_otp_hash)
