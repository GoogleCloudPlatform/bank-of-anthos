from time import sleep
import os

# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import serialization

from google.cloud import kms_v1

from flask import Flask

_project_id = os.getenv('KEY_PROJECT_ID')
_keyring = os.getenv('RING_ID')
_client = kms_v1.KeyManagementServiceClient()

app = Flask(__name__)

@app.route('/key', methods=['GET'])
def get_public_key():
    branch_id='bank-0'
    key_version='1'
    key_path = ("projects/{}/locations/global/keyRings/{}/cryptoKeys"
              "/{}/cryptoKeyVersions/{}".format(_project_id, _keyring,\
              branch_id, key_version))
    response = _client.get_public_key(key_path)
    key_txt = response.pem.encode('ascii')
    print(key_txt)
    #key = serialization.load_pem_public_key(key_txt, default_backend())
    return key_txt, 201

if __name__ == '__main__':
    for v in ['PORT', 'KEY_PROJECT_ID', 'RING_ID']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
