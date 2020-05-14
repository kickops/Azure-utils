import base64
import boto3

def decrypt(secret):
    session = boto3.session.Session()
    client = session.client('kms', region_name='us-east-1')
    plaintext = client.decrypt(CiphertextBlob=bytes(base64.b64decode(secret)))
    value = plaintext["Plaintext"]
    return value.decode("utf-8")
