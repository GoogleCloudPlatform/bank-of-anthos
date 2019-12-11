import logging
import os

from pymongo import MongoClient

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/new_user', methods=['POST'])
def add_user():
    user_req = request.get_json()
    logging.info('adding user: %s' % str(trans_obj))

    insert_user(create_user(user_req))
    return jsonify({}), 201


def create_user(user_req)
    user = user_req.username
    return user

def insert_user(user)
    client = MongoClient()
    db = client['test_db']
    users = db.users
    users.insert_one(user)
    


if __name__ == '__main__':
    for v in ['PORT']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
