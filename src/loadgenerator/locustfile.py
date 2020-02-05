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

def create_account(l, username):
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
    l.client.post("/signup", data=userdata)
    print("created user: {}".format(username))

def view_index(l):
    l.client.get("/")

def view_home(l):
    l.client.get("/home")

def view_login(l):
    l.client.get("/login")

def view_signup(l):
    l.client.get("/signup")

def login(l, username):
    l.locust.username = username
    l.client.post("/login", {"username":username,
                             "password":MASTER_PASSWORD})

def logout(l):
    l.client.post("/logout")
    l.locust.username = None

def relogin(l):
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
        create_account(self, "user")
        # create test accounts
        for username in userlist:
            create_account(self, username)

    def on_start(self):
        username = random.choice(userlist)
        login(self, username)

    tasks = {
        # view_index: 3,
        # view_home: 3,
        # view_login: 3,
        # view_signup: 3,
        relogin:1
    }

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 10000
