from time import sleep
import os

# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import serialization

from google.cloud import kms_v1

from flask import Flask, request

_keyring = os.getenv('KEYRING')
_client = kms_v1.KeyManagementServiceClient()

app = Flask(__name__)

@app.route('/key', methods=['GET'])
def get_public_key():
    branch_id = request.args.get('branch_id')
    key_version = request.args.get('key_version')

    key_path = ("{}/cryptoKeys/{}/cryptoKeyVersions/{}".format(
        _keyring, branch_id, key_version))
    response = _client.get_public_key(key_path)
    key_txt = response.pem.encode('ascii')
    print(key_txt)
    return key_txt, 201

if __name__ == '__main__':
    for v in ['PORT', 'KEYRING']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
