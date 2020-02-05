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
from locust import HttpLocust, TaskSet

userlist = ["testuser-%i".format(i) for i in range(100)]

def create_accounts(l):
    for username in userlist:
        userdata = { "username":username,
                     "password":"test",
                     "password-repeat":"test",
                     "firstname": username,
                     "lastname":"TestAccount",
                     "birthday":"01/01/2000"
                    }
        l.client.post(signup, data=userdata)

def view_index(l):
    l.client.get("/")

def view_home(l):
    l.client.get("/home")

def view_login(l):
    l.client.get("/login")

def view_signup(l):
    l.client.get("/signup")

class UserBehavior(TaskSet):
    def setup(self):
        create_accounts(l)

    def on_start(self):
        view_index(self)

    tasks = {
        view_index: 1,
        view_home: 1,
        view_login: 1,
        view_signup: 1
    }

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 10000
