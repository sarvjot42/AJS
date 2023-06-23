import os
import traceback
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

try:
    account_url = "https://sarvjot.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    container_name = "jstacks"
    container_client = blob_service_client.get_container_client(container_name)

    local_path = ".."
    local_file_name = "script1.py"
    upload_file_path = os.path.join(local_path, local_file_name)

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    with open(upload_file_path, "rb") as f:
        data = f.read()
        blob_client.upload_blob(data)

    print(blob_client.url)

except Exception as ex:
    print(traceback.format_exc())
