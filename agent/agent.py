import os
import time
import paramiko
import boto3
import gzip
import shutil
import socket


# Load environment variables
REGION = os.getenv("REGION")
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")
FTP_TARGET_DIR = os.getenv("FTP_TARGET_DIR")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

# AWS Clients
boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
logs_client = boto3.client("logs")
sns_client = boto3.client("sns")

SAMPLE_FILE = "/mnt/sample.csv"
COMPRESSED_FILE = "/mnt/sample.csv.gz"

def log_to_cloudwatch(message):
    """Log to AWS CloudWatch, ensuring the log stream exists first"""
    log_group_name = "CSV_Agent_Logs"
    log_stream_name = REGION  # Each agent gets its own log stream

    try:
        # Check if log stream exists
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            logStreamNamePrefix=log_stream_name
        )

        # If no streams exist with the prefix, create one
        if not response.get("logStreams"):
            print(f"⚠ Log stream {log_stream_name} not found. Creating it now...")
            logs_client.create_log_stream(
                logGroupName=log_group_name,
                logStreamName=log_stream_name
            )
            time.sleep(3)  # Wait for AWS to register the new stream

    except logs_client.exceptions.ResourceNotFoundException as e:
        print(f"❌ Log group {log_group_name} does not exist. Error: {str(e)}")
        return

    try:
        logs_client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            logEvents=[{"timestamp": int(time.time() * 1000), "message": message}]
        )
        print(f"📝 Logged to CloudWatch: {message}")
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"❌ Failed to log message: {message}. Log stream still does not exist.")

def send_sns_alert(message):
    """Send alert to SNS"""
    sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="CSV Agent Alert")

def compress_file():
    """Compress a file using Gzip"""
    with open(SAMPLE_FILE, 'rb') as f_in, gzip.open(COMPRESSED_FILE, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"✅ Compressed {SAMPLE_FILE} -> {COMPRESSED_FILE}")
    log_to_cloudwatch(f"Compressed {SAMPLE_FILE} -> {COMPRESSED_FILE}")

def upload_to_sftp():
    """Upload file to SFTP with retries and debug information"""
    attempts = 5
    delay = 3  # Wait 3 seconds between retries

    print(f"📂 Checking file existence: {COMPRESSED_FILE}")
    if not os.path.exists(COMPRESSED_FILE):
        print(f"❌ File {COMPRESSED_FILE} does not exist. Aborting upload.")
        return

    for attempt in range(attempts):
        try:
            # Resolve SFTP hostname
            sftp_ip = socket.gethostbyname(FTP_HOST)
            print(f"🔍 Resolved SFTP hostname '{FTP_HOST}' to {sftp_ip}")

            # Connect to SFTP
            transport = paramiko.Transport((FTP_HOST, 22))
            transport.connect(username=FTP_USER, password=FTP_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Check remote directory existence
            print(f"📂 Checking remote directory: {FTP_TARGET_DIR}")
            try:
                sftp.stat(FTP_TARGET_DIR)
            except FileNotFoundError:
                print(f"⚠ Remote directory {FTP_TARGET_DIR} does not exist. Creating it...")
                sftp.mkdir(FTP_TARGET_DIR)

            # Upload file
            remote_path = os.path.join(FTP_TARGET_DIR, os.path.basename(COMPRESSED_FILE))
            print(f"📤 Uploading {COMPRESSED_FILE} -> {remote_path}")
            sftp.put(COMPRESSED_FILE, remote_path)

            print(f"✅ Uploaded {COMPRESSED_FILE} to SFTP")
            log_to_cloudwatch(f"Uploaded {COMPRESSED_FILE} to SFTP")

            sftp.close()
            transport.close()
            return

        except Exception as e:
            print(f"❌ Upload failed (attempt {attempt + 1}/{attempts}): {str(e)}")
            log_to_cloudwatch(f"SFTP Upload Failed: {str(e)}")

        time.sleep(delay)

    print("❌ SFTP upload completely failed after retries.")
    send_sns_alert("SFTP upload failed after multiple attempts.")

if __name__ == "__main__":
    print(f"🚀 Agent started in region {REGION}")
    log_to_cloudwatch(f"Agent started in {REGION}")
    send_sns_alert(f"Agent started in {REGION}")

    compress_file()
    upload_to_sftp()
