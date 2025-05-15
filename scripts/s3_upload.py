import boto3


def upload_to_s3(model_files, bucket_name, aws_access_key, aws_secret_key, region_name='us-east-1'):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )
    for local_path, s3_key in model_files.items():
        s3.upload_file(local_path, bucket_name, s3_key)
        print(f"✅ Uploaded {local_path} to s3://{bucket_name}/{s3_key}")
