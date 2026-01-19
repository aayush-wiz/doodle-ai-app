import requests
import uuid
import sys
import os

# Ensure backend dir is in path to import storage
sys.path.append(os.path.dirname(__file__))

from storage import upload_file_to_r2, create_presigned_url

BASE_URL = "http://localhost:8000"

def test_auth():
    print("Testing Auth...")
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "testpassword123"

    # Register
    print(f"Registering {username}...")
    try:
        resp = requests.post(f"{BASE_URL}/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        if resp.status_code != 200:
            print(f"Registration failed: {resp.text}")
            return
        print("Registration success!")
        user_id = resp.json()["id"]
    except Exception as e:
        print(f"Auth test failed connection: {e}")
        return

    # Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/token", json={
        "username": username,
        "email": email,
        "password": password
    })
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    print(f"Login success! Token: {token[:10]}...")

def test_r2():
    print("\nTesting R2 Storage...")
    dummy_filename = "test_upload.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is a test file for R2 upload.")
    
    try:
        print(f"Uploading {dummy_filename} to R2...")
        object_name = f"test_{uuid.uuid4().hex}.txt"
        key = upload_file_to_r2(dummy_filename, object_name)
        
        if key:
            print(f"Upload success! Key: {key}")
            # Test presigned URL generation
            url = create_presigned_url(key)
            print(f"Presigned URL: {url}")
        else:
            print("Upload failed (returned None).")
            
    except Exception as e:
        # Check if credential error
        import traceback
        traceback.print_exc()
        print(f"R2 test failed: {e}")
    finally:
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)

if __name__ == "__main__":
    # Check if backend is running for auth test
    try:
        # Timeout 2s
        requests.get(f"{BASE_URL}/health", timeout=2)
        test_auth()
    except Exception as e:
        print(f"Backend not running or healthy ({e}), skipping Auth API test.", flush=True)
        
    test_r2()
