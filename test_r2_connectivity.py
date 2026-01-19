import os
import boto3
from dotenv import load_dotenv

load_dotenv(dotenv_path='backend/.env')

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

print(f"Connecting to R2 Bucket: {R2_BUCKET_NAME}")

s3 = boto3.client(
    service_name='s3',
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto", 
)

try:
    # List one object
    print("Listing objects...")
    response = s3.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=5)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            print(f"Found object: {key}")
            
            # Generate Presigned URL
            url = s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': R2_BUCKET_NAME, 'Key': key},
                ExpiresIn=3600
            )
            print(f"Presigned URL: {url}")
            break
    else:
        print("Bucket is empty or no objects found.")

except Exception as e:
    print(f"Error: {e}")
