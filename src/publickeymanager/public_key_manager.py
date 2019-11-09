from time import sleep
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from google.cloud import kms_v1

_project_id = os.getenv('KEY_PROJECT_ID')
_keyring = os.getenv('RING_ID')
_client = kms_v1.KeyManagementServiceClient()

def get_public_key(branch_id, key_version):
    key_path = ("projects/{}/locations/global/keyRings/{}/cryptoKeys"
              "/{}/cryptoKeyVersions/{}".format(_project_id, _keyring,\
              branch_id, key_version))
    response = _client.get_public_key(key_path)
    key_txt = response.pem.encode('ascii')
    #key = serialization.load_pem_public_key(key_txt, default_backend())
    return key_txt

if __name__ == '__main__':
    key = get_public_key('bank-0', '1')

    while True:
        print('hello: {} {}'.format(_project_id, _keyring))
        print(key)
        sleep(10)
