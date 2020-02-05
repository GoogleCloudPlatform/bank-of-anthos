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

userlist = ["testuser-%i".format(i) for i in range(100)]

def create_account(l, username, password="password"):
    userdata = { "username":username,
                 "password":password,
                 "password-repeat":password,
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
    print("creating user: {}".format(userdata))
    l.client.post("/signup", data=userdata)

def view_index(l):
    l.client.get("/")

def view_home(l):
    l.client.get("/home")

def view_login(l):
    l.client.get("/login")

def view_signup(l):
    l.client.get("/signup")

def login(l):
    l.client.post("/login", {"username":l.locust.username, "password":l.locust.password})

def logout(l):
    l.client.post("/logout")

def relogin(l):
    logout(l)
    sleep(1)
    view_login(l)
    sleep(1)
    view_signup(l)
    sleep(1)
    login(l)


class UserBehavior(TaskSet):
    def setup(self):
        # create user account
        create_account(self, "user", "password")

    def on_start(self):
        self.locust.username = str(uuid.uuid4())
        self.locust.password = "password"
        create_account(self, self.locust.username, self.locust.password)
        print("created user: {}".format(self.locust.username))

    # tasks = {
    #     view_index: 1,
    #     view_home: 1,
    #     view_login: 1,
    #     view_signup: 1
    # }
    tasks = [relogin]

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 10000
