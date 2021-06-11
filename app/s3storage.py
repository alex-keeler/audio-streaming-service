import logging
import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = "audio-test-1468"

def create_presigned_url(BUCKET_NAME, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def upload_file(BUCKET_NAME, filename, object_name):
    s3_client = boto3.client('s3')
    s3_client.upload_file(filename, BUCKET_NAME, object_name)

    # Bucket = bucket_name,
    # Filename=filename,
    # Key = filename,

    return "Upload complete!"

def delete_file(bucket_name, object_name):
    s3_client = boto3.client('s3')
    s3_client.delete_object(Bucket=bucket_name, Key=object_name)