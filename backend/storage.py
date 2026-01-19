import boto3
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

# Explicitly strip to avoid hidden characters
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "").strip()
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev").strip()

def get_r2_client():
    if not R2_ACCOUNT_ID or "placeholder" in R2_ACCOUNT_ID:
        print("Warning: R2_ACCOUNT_ID is not set correctly.")
        return None

    # Clean env to prevent boto3 from picking up AWS keys
    env_copy = os.environ.copy()
    if "AWS_ACCESS_KEY_ID" in env_copy:
        del env_copy["AWS_ACCESS_KEY_ID"]
    if "AWS_SECRET_ACCESS_KEY" in env_copy:
        del env_copy["AWS_SECRET_ACCESS_KEY"]

    session = boto3.Session()
    return session.client(
        's3',
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto"
    )

def upload_file_to_r2(file_path: str, object_name: str = None) -> str:
    """Upload a file to an R2 bucket and return the public URL (if configured) or Key"""
    if object_name is None:
        object_name = os.path.basename(file_path)

    s3_client = get_r2_client()
    if not s3_client:
        return None

    try:
        s3_client.upload_file(file_path, R2_BUCKET_NAME, object_name)
        print(f"Uploaded {file_path} to R2 bucket {R2_BUCKET_NAME} as {object_name}")
        return object_name

    except FileNotFoundError:
        print("The file was not found")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        return None

def create_presigned_url(object_name: str, expiration=3600) -> str:
    """Generate a presigned URL to share an S3 object"""
    s3_client = get_r2_client()
    if not s3_client:
        return None
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': R2_BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None

def get_public_url(object_name: str) -> str:
    """Get the public R2 URL for an object"""
    return f"{R2_PUBLIC_URL}/{object_name}"
