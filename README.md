# Encryption Service with Kubernetes and MinIO

This project implements an **Encryption and Decryption Service** built using **FastAPI**, **MinIO**, and **KMS (Key Management Service)**. The service allows users to upload files, encrypt them using a KMS-managed key, store them in MinIO, and later download and decrypt the files using the same key. This project is containerized and deployed to a **Minikube** Kubernetes cluster.

## Features

- **File Upload**: Upload files to be encrypted.
- **Encryption**: Encrypt files using a KMS-managed key.
- **File Storage**: Store encrypted files in **MinIO** (object storage).
- **File Listing**: List all uploaded encrypted files.
- **File Download and Decryption**: Retrieve encrypted files and decrypt them using the correct key.
- **Kubernetes Deployment**: Containerized and deployed on **Minikube** for local testing.

## Architecture

1. **FastAPI Backend**: The backend is built using FastAPI to expose endpoints for uploading, downloading, and listing encrypted files.
2. **KMS**: A Key Management Service (KMS) is used to generate and manage encryption keys. The keys are used to encrypt and decrypt the files.
3. **MinIO**: MinIO is used as object storage for storing encrypted files. It provides S3-compatible object storage in a Kubernetes environment.
4. **Containerization**: The application is containerized using Docker and deployed on a **Minikube** Kubernetes cluster.
5. **Load Testing**: Locust is used for simulating multiple users to test the scalability of the encryption service.

## Key Management Service (KMS)

The **KMS** is a core part of the project, responsible for securely managing encryption keys used for encrypting and decrypting files. The KMS provides the following endpoints:

### 1. `POST /kms/generate-key/`
- **Description**: Generates a new encryption key using a PBKDF2 algorithm with a random plain key and salt.
- **Response**:
  - `key_id`: The unique identifier for the generated key.
  - `message`: Success message confirming key generation.

### 2. `GET /kms/retrieve-key/{key_id}`
- **Description**: Retrieves the encryption key by its `key_id`. The key is regenerated using the stored plain key and salt using PBKDF2.
- **Response**:
  - `key_id`: The ID of the requested key.
  - `key`: The regenerated encryption key in hexadecimal format.

### 3. `DELETE /kms/delete-key/{key_id}`
- **Description**: Deletes the encryption key by its `key_id`.
- **Response**:
  - `key_id`: The ID of the key that was deleted.
  - `message`: Success message confirming key deletion.

## Endpoints for File Encryption Service

### 1. `POST /encryption/upload/`
- **Description**: Uploads and encrypts a file using the KMS-managed key.
- **Request Parameters**:
  - `file`: The file to be uploaded (Multipart form data).
  - `key_id`: The ID of the encryption key to use for the file encryption.
- **Response**:
  - `message`: A success message if the file is successfully uploaded and encrypted.
  - `filename`: The name of the encrypted file stored in MinIO.

### 2. `GET /encryption/download/{filename}`
- **Description**: Downloads and decrypts a file.
- **Request Parameters**:
  - `filename`: The name of the encrypted file.
  - `key_id`: The ID of the decryption key.
- **Response**:
  - The decrypted file is streamed back to the user.

### 3. `GET /encryption/files/`
- **Description**: Lists all the encrypted files in MinIO.
- **Response**:
  - A list of encrypted file names stored in the MinIO bucket.

## Setup Instructions

### Prerequisites

Before setting up the project, ensure you have the following installed:

- **Docker**: For containerizing the application and MinIO.
- **Minikube**: For running a local Kubernetes cluster.
- **kubectl**: For interacting with the Kubernetes cluster.
- **Python 3.8+**: For running the FastAPI app and other dependencies.
- **Locust**: For load testing.

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Start minikube cluster

Start the minikube cluster and switch the docker environment to the one inside minikube
```bash
minikube start --driver=docker --memory=4096 --cpus=2
eval $(minikube docker-env)
```
These commands are for WSL2, therefore I had to specify the driver, and increase the memory associated when starting the minikube container

### 3. Build the services

Build the docker images for the **encryption** and **key management service**. Since we switched the docker environment these would be built inside the minikube container.
```bash
docker build -t kms-service:latest ./services/kms
docker build -t encryption-service:latest ./services/encryption
```

### 4. Deploy all the various services

Deploy all the various services needed by the application
```bash
kubectl apply -f encryption-deployment.yaml
kubectl apply -f kms-deployment.yaml
kubectl apply -f ingress.yaml
kubectl apply -f minio-deployment.yaml
```

### 5. Enabling Addons on Minikube

Enable ingress and metrics server addons on minikube
```bash
minikube addons enable metrics-server
minikube addons enable ingress
```

### 6.1 Testing locally

For testing locally following curl commands can be used
```bash
curl -X POST "http://192.168.49.2/kms/generate-key/"
curl -X POST -F "file=@example.txt" "http://192.168.49.2/encryption/upload/?key_id=<generated-key-id>"
curl -JO "http://192.168.49.2/encryption/download/example.txt.enc?key_id=<generated-key-id>"
```

### 6.2 Testing with locust

For testing with locust make sure it is installed
```bash
python3 -m locust -f locustfile.py --host=http://<minikube-ip>
```
