from fastapi import FastAPI, HTTPException
from uuid import uuid4
from pathlib import Path
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

app = FastAPI()

KEYS_DIR = Path("keys")
KEYS_DIR.mkdir(exist_ok=True)

def generate_key_from_password(plain_key: bytes, salt: bytes) -> bytes:
    """Generate a 32-byte encryption key using PBKDF2."""
    return PBKDF2(plain_key, salt, dkLen=32)

@app.post("/kms/generate-key/")
def generate_key():
    """Generate a new encryption key using PBKDF2."""
    key_id = str(uuid4())
    
    plain_key = get_random_bytes(16)
    salt = get_random_bytes(16)
    
    key = generate_key_from_password(plain_key, salt)
    
    key_path = KEYS_DIR / key_id
    with open(key_path, "wb") as f:
        f.write(plain_key + salt)
    
    return {"key_id": key_id, "message": "Key generated successfully"}

@app.get("/kms/retrieve-key/{key_id}")
def retrieve_key(key_id: str):
    """Retrieve an encryption key by its ID."""
    key_path = KEYS_DIR / key_id
    if not key_path.exists():
        raise HTTPException(status_code=404, detail="Key not found")
    
    with open(key_path, "rb") as f:
        plain_key_and_salt = f.read()
    
    plain_key = plain_key_and_salt[:16]
    salt = plain_key_and_salt[16:]
    
    key = generate_key_from_password(plain_key, salt)
    
    return {"key_id": key_id, "key": key.hex()}

@app.delete("/kms/delete-key/{key_id}")
def delete_key(key_id: str):
    """Delete a key by its ID."""
    key_path = KEYS_DIR / key_id
    if not key_path.exists():
        raise HTTPException(status_code=404, detail="Key not found")
    key_path.unlink()
    return {"key_id": key_id, "message": "Key deleted successfully"}
