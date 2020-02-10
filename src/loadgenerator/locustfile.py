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
from locust import HttpLocust, TaskSet, TaskSequence, task
import sys

MASTER_PASSWORD="password"

userlist = []

def _signup_helper(self, username):
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
    with self.client.post("/signup", data=userdata, catch_response=True) as response:
        if response.url is None or "Error" in response.url:
            response.failure("signup failed")
            return False
        else:
            print("created user: {}".format(username))
            return True


class AuthenticatedTasks(TaskSet):

    @task(5)
    def view_index(self):
        """
        load the / page
        fails if not logged on (redirets to /login)
        """
        with self.client.get("/", catch_response=True) as response:
            for h in response.history:
                if h.status_code > 200 and h.status_code < 400:
                    response.failure("Got redirect")

    @task(5)
    def view_home(self):
        """
        load the /home page (identical to /)
        fails if not logged on (redirets to /login)
        """
        with self.client.get("/home", catch_response=True) as response:
            for h in response.history:
                if h.status_code > 200 and h.status_code < 400:
                    response.failure("Got redirect")


    @task(1)
    def logout(self):
        """
        sends a /logout POST request
        fails if not logged in
        """
        self.client.post("/logout")
        self.locust.username = None
        # go to UnauthenticatedTasks
        self.interrupt()

class UnauthenticatedTasks(TaskSet):

    @task(5)
    def view_login(self):
        """
        load the /login page
        fails if already logged on (redirets to /home)
        """
        with self.client.get("/login", catch_response=True) as response:
            for h in response.history:
                if h.status_code > 200 and h.status_code < 400:
                    response.failure("Got redirect")

    @task(5)
    def view_signup(self):
        """
        load the /signup page
        self.locust.username = str(uuid.uuid4())
        fails if not logged on (redirets to /home)
        """
        with self.client.get("/signup", catch_response=True) as response:
            for h in response.history:
                if h.status_code > 200 and h.status_code < 400:
                    response.failure("Got redirect")

    @task(1)
    def signup_and_login(self):
        # sign up
        new_username = str(uuid.uuid4())
        success = _signup_helper(self, new_username)
        if success:
            # login
            with self.client.post("/login", {"username":new_username,
                    "password":MASTER_PASSWORD}, catch_response=True) as response:
                print(response.url)
                if response.url is None or "login" in response.url:
                    response.failure("login failed")
                elif response.status_code == 200:
                    # go to AuthenticatedTasks
                    response.success()
                    self.locust.username = new_username
                    userlist.append(new_username)
                    self.interrupt()

class AllTasks(TaskSequence):
    tasks = [UnauthenticatedTasks, AuthenticatedTasks]

class WebsiteUser(HttpLocust):
    task_set = AllTasks
    min_wait = 1000
    max_wait = 10000
