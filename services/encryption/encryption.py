from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import requests

def derive_key(plain_key: bytes, salt: bytes) -> bytes:
    """Generate a key using PBKDF2 from the plain_key and salt."""
    return PBKDF2(plain_key, salt, dkLen=32)

def encrypt_file(data: bytes, password: str) -> tuple:
    """Encrypts a file and returns ciphertext, nonce, tag, and salt."""
    salt = get_random_bytes(16)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(pad(data, 16))
    return ciphertext, cipher.nonce, tag, salt

def decrypt_file(ciphertext: bytes, nonce: bytes, tag: bytes, salt: bytes, password: str) -> bytes:
    """Decrypts the file and returns plain data."""
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return unpad(cipher.decrypt_and_verify(ciphertext, tag), 16)

def get_key_from_kms(key_id: str, kms_url: str = "http://kms-service:8001"):
    """Retrieve a key from the simulated KMS."""
    response = requests.get(f"{kms_url}/kms/retrieve-key/{key_id}")
    response.raise_for_status()
    return bytes.fromhex(response.json()["key"])
