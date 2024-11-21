from locust import HttpUser, task, between, LoadTestShape
import random
import string
from io import BytesIO

class KMSEncryptionUser(HttpUser):
    wait_time = between(1, 3)
    key_id = None
    key_id_map = {}
    sample_file_content = b"This is a sample file for encryption testing."

    def generate_random_filename(self):
        """Generate a random filename."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + ".txt"

    @task(1)
    def generate_key(self):
        """Generate a new encryption key."""
        response = self.client.post("/kms/generate-key/")
        if response.status_code == 200:
            self.key_id = response.json().get("key_id")
            print(f"Generated key_id: {self.key_id}")
        else:
            print(f"Failed to generate key: {response.status_code} {response.text}")
        
        """Upload and encrypt a file using the generated key."""
        if not self.key_id:
            print("No key_id available for encryption.")
            return
        
        file_name = self.generate_random_filename()
        response = self.client.post(
            f"/encryption/upload/?key_id={self.key_id}",
            files={"file": (file_name, BytesIO(self.sample_file_content))}
        )
        if response.status_code == 200:
            print(f"File {file_name} uploaded and encrypted successfully!")
            self.key_id_map[file_name] = self.key_id
        else:
            print(f"Failed to upload file: {response.status_code} {response.text}")

        """Download and decrypt a file."""
        if not self.key_id:
            print("No key_id available for decryption.")
            return
        
        key_id = self.key_id_map.get(file_name)

        if key_id:
            response = self.client.get(f"/encryption/download/{file_name}.enc", params={"key_id": key_id})
            if response.status_code == 200:
                print(f"File {file_name} downloaded and decrypted successfully!")
            else:
                print(f"Failed to download file: {response.status_code} {response.text}")
        else:
            print(f"No key_id found for file {file_name}")
        


class CustomLoadTestShape(LoadTestShape):
    """
    A custom load test shape to simulate different stages of load testing.
    """
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 1},
        {"duration": 120, "users": 40, "spawn_rate": 2},
        {"duration": 180, "users": 100, "spawn_rate": 5},    
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
