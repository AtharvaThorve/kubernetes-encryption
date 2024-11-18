from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from minio import Minio
from encryption import encrypt_file, decrypt_file, get_key_from_kms

KMS_URL = "http://kms-service:8001"
BUCKET_NAME = "encrypted-files"

app = FastAPI()

minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
        print("Created Bucket")
except Exception as e:
    print(f"Error creating bucket: {e}")

@app.post("/encryption/upload/")
async def upload_file(file: UploadFile, key_id: str):
    """Encrypt and upload a file using a KMS-managed key."""
    content = await file.read()
    
    key = get_key_from_kms(key_id, KMS_URL)
    
    ciphertext, nonce, tag, salt = encrypt_file(content, key)
    
    encrypted_data = salt + nonce + tag + ciphertext
    
    encrypted_buffer = BytesIO(encrypted_data)
    encrypted_buffer.seek(0)
    
    encrypted_filename = f"{file.filename}.enc"
    try:
        minio_client.put_object(
            BUCKET_NAME,
            encrypted_filename,
            encrypted_buffer,
            length=len(encrypted_data)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to MinIO: {str(e)}")

    return {
        "message": "File encrypted and uploaded successfully!",
        "filename": encrypted_filename
    }

@app.get("/encryption/download/{filename}")
async def download_file(filename: str, key_id: str):
    """Decrypt and stream a file from MinIO."""
    try:
        response = minio_client.get_object(BUCKET_NAME, filename)
        data = response.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

    key = get_key_from_kms(key_id, KMS_URL)

    salt, nonce, tag, ciphertext = data[:16], data[16:32], data[32:48], data[48:]

    try:
        plaintext = decrypt_file(ciphertext, nonce, tag, salt, key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")
    
    file_stream = BytesIO(plaintext)
    download_filename = filename.replace('.enc', '.dec')

    return StreamingResponse(
        file_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"'
        }
    )

@app.get("/encryption/files/")
async def list_files():
    """List all encrypted files in the MinIO bucket."""
    try:
        objects = minio_client.list_objects(BUCKET_NAME)
        files = [obj.object_name for obj in objects]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
