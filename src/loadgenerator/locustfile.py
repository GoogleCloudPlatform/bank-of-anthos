#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import uuid
from time import sleep
from locust import HttpLocust, TaskSet

MASTER_PASSWORD="password"

userlist = ["testuser-{}".format(i) for i in range(10)]

def _signup_helper(l, username, report_failures=True):
    """
    create a new user account in the system
    """
    userdata = { "username":username,
                 "password":MASTER_PASSWORD,
                 "password-repeat":MASTER_PASSWORD,
                 "firstname": username,
                 "lastname":"TestAccount",
                 "birthday":"01/01/2000",
                 "timezone":"82",
                 "address":"1021 Valley St",
                 "city":"Seattle",
                 "state":"WA",
                 "zip":"98103",
                 "ssn":"111-22-3333"
    }
    with l.client.post("/signup", data=userdata, catch_response=True) as response:
        if not report_failures:
            response.success()
        elif "Error" in response.url:
            response.failure("signup failed")
    print("created user: {}".format(username))

def view_index(l):
    """
    load the / page
    fails if not logged on (redirets to /login)
    """
    with l.client.get("/", catch_response=True) as response:
        for h in response.history:
            if h.status_code > 200 and h.status_code < 400:
                response.failure("Got redirect")

def view_home(l):
    """
    load the /home page (identical to /)
    fails if not logged on (redirets to /login)
    """
    with l.client.get("/home", catch_response=True) as response:
        for h in response.history:
            if h.status_code > 200 and h.status_code < 400:
                response.failure("Got redirect")

def view_login(l):
    """
    load the /login page
    fails if already logged on (redirets to /home)
    """
    with l.client.get("/login", catch_response=True) as response:
        for h in response.history:
            if h.status_code > 200 and h.status_code < 400:
                response.failure("Got redirect")

def view_signup(l):
    """
    load the /signup page
    fails if not logged on (redirets to /home)
    """
    with l.client.get("/signup", catch_response=True) as response:
        for h in response.history:
            if h.status_code > 200 and h.status_code < 400:
                response.failure("Got redirect")

def signup(l):
    _signup_helper(l, uuid.uuid4(), report_failures=True)

def login(l, username):
    """
    sends a /login POST request
    fails if credentials are invalid
    """
    l.locust.username = username
    with l.client.post("/login", {"username":username, "password":MASTER_PASSWORD}, catch_response=True) as response:
        if "login" in response.url:
            response.failure("login failed")

def logout(l):
    """
    sends a /logout POST request
    fails if not logged in
    """
    l.client.post("/logout")
    l.locust.username = None

def relogin(l):
    """
    log out of current account and into a new one
    also test loading pages only accessible when unauthenticated
    """
    logout(l)
    sleep(1)
    view_login(l)
    sleep(1)
    view_signup(l)
    sleep(1)
    new_username = random.choice(userlist)
    login(l, new_username)


class UserBehavior(TaskSet):
    def setup(self):
        # create user account
        _signup_helper(self, "user", report_failures=False)
        # create test accounts
        for username in userlist:
            _signup_helper(self, username, report_failures=False)

    def on_start(self):
        username = random.choice(userlist)
        login(self, username)

    tasks = {
        view_index:1,
        view_home:1,
        relogin:1,
        signup:1
    }

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 10000
