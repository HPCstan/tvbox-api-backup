import os
import sys
import mimetypes
import boto3
from botocore.config import Config

# R2 Configuration from Environment Variables
ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID')
ACCESS_KEY = os.environ.get('R2_ACCESS_KEY_ID')
SECRET_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')

if not all([ACCOUNT_ID, ACCESS_KEY, SECRET_KEY, BUCKET_NAME]):
    print("Error: Missing R2 credentials in environment variables.")
    sys.exit(1)

# Initialize S3 client for Cloudflare R2
s3 = boto3.client(
    service_name='s3',
    endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version='s3v4')
)

# Files and directories to upload
UPLOAD_TARGETS = [
    'list.txt',
    'SUMMARY.txt',
    'livelist.txt',
    'tvbox',
    'ry'
]

def get_content_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.m3u':
        return 'application/vnd.apple.mpegurl'
    if ext == '.json':
        return 'application/json'
    if ext == '.txt':
        return 'text/plain'
    return 'application/octet-stream'

def upload_file(local_path, s3_key):
    try:
        content_type = get_content_type(local_path)
        print(f"Uploading {local_path} -> {s3_key} ({content_type})")
        s3.upload_file(
            local_path,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
    except Exception as e:
        print(f"Failed to upload {local_path}: {e}")

def main():
    repo_root = os.getcwd()
    
    for target in UPLOAD_TARGETS:
        target_path = os.path.join(repo_root, target)
        
        if not os.path.exists(target_path):
            print(f"Skip: {target} not found.")
            continue
            
        if os.path.isfile(target_path):
            # Upload single file
            upload_file(target_path, target)
        elif os.path.isdir(target_path):
            # Upload directory recursively
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    # Calculate relative path to use as S3 key
                    s3_key = os.path.relpath(local_file_path, repo_root)
                    # Convert windows backslashes to forward slashes for S3
                    s3_key = s3_key.replace('\\', '/')
                    upload_file(local_file_path, s3_key)

if __name__ == '__main__':
    print("Starting upload to Cloudflare R2...")
    main()
    print("Upload complete!")
