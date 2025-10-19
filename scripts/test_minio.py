from minio import Minio
from minio.error import S3Error
import os
import io

def test_minio_operations():
    minio_client = Minio(
        endpoint="172.22.121.50:31410",
        access_key="rHk6why0Un5gK6ntvX2Q",
        secret_key="3GbrIJrNvnk7kitCZWQ0JlrkGzRoESo7tvtdHMIt",
        secure=False
    )

    # Test bucket name
    bucket_name = "etl"
    
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created successfully")
        else:
            print(f"Bucket '{bucket_name}' already exists")

        # Create a test file in memory
        content = io.BytesIO(b"Hello MinIO!")
        content_size = len(content.getvalue())

        # Upload the test file
        object_name = "teach_spider/hello.txt"
        minio_client.put_object(
            bucket_name,
            object_name,
            content,
            content_size,
            content_type="text/plain"
        )
        print(f"File '{object_name}' uploaded successfully")

        # List all objects in the bucket
        print("\nObjects in bucket:")
        objects = minio_client.list_objects(bucket_name)
        for obj in objects:
            print(f" - {obj.object_name} (size: {obj.size} bytes)")

        # Download the file
        try:
            data = minio_client.get_object(bucket_name, object_name)
            print(f"\nDownloaded content: {data.read().decode()}")
        finally:
            data.close()
            data.release_conn()

        # Remove the test file
        # minio_client.remove_object(bucket_name, object_name)
        print(f"\nFile '{object_name}' removed successfully")

    except S3Error as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_minio_operations()
