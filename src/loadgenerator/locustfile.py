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
from locust import HttpLocust, TaskSet, TaskSequence, task, seq_task
import sys
from random import randint
import json
import os


MASTER_PASSWORD="password"

def signup_helper(l, username):
    """
    create a new user account in the system
    succeeds if token was returned
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
        found_token = False
        for r in response.history:
            found_token |= r.cookies.get('token') is not None
        if found_token:
            response.success()
            print("created user: {}".format(username))
        else:
            response.failure("login failed")
        return found_token

class AllTasks(TaskSequence):
    def setup(self):
        """
        Before starting, attempt to create one account
        If it fails, the system isn't ready. Crash and try again
        """
        new_username = str(uuid.uuid4())
        success = signup_helper(self, new_username)
        if not success:
            print("failed to create account. Abort")
            sys.exit(1)
        else:
            self.client.post("/logout")

    @seq_task(1)
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
            fails if not logged on (redirets to /home)
            """
            with self.client.get("/signup", catch_response=True) as response:
                for h in response.history:
                    if h.status_code > 200 and h.status_code < 400:
                        response.failure("Got redirect")

        @task(1)
        def signup(self):
            """
            sends POST request to /signup to create a new user
            on success, exits UnauthenticatedTasks
            """
            # sign up
            new_username = str(uuid.uuid4())
            success = signup_helper(self, new_username)
            if success:
                # go to AuthenticatedTasks
                self.locust.username = new_username
                self.interrupt()

    @seq_task(2)
    class AuthenticatedTasks(TaskSet):
        def on_start(self):
            self.deposit(1e9, 1e9)

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

        @task(50)
        def payment(self, min_val=1, max_val=1000):
            """
            POST to /payment, sending money to other account
            """
            transaction = { "account_num":str(randint(100000000, 999999999)),
                            "amount":randint(min_val, max_val)
                          }
            with self.client.post("/payment", data=transaction, catch_response=True) as response:
                print("payment: ", response)

        @task(5)
        def deposit(self, min_val=1, max_val=1000):
            """
            POST to /deposit, depositing external money into account
            """
            account_info = {"account_num":str(randint(100000000, 999999999)),
                            "routing_num":"111111111"
                           }
            transaction = { "account": json.dumps(account_info),
                            "amount":randint(min_val, max_val)
                          }
            with self.client.post("/deposit", data=transaction, catch_response=True) as response:
                print("deposit: ", response)

        @task(2)
        def login(self):
            """
            sends POST request to /login with stored credentials
            succeeds if a token was returned
            """
            with self.client.post("/login", {"username":self.locust.username,
                                             "password":MASTER_PASSWORD},
                                             catch_response=True) as response:
                found_token = False
                for r in response.history:
                    found_token |= r.cookies.get('token') is not None
                if found_token:
                    response.success()
                else:
                    response.failure("login failed")

        @task(1)
        def logout(self):
            """
            sends a /logout POST request
            fails if not logged in
            exits AuthenticatedTasks
            """
            self.client.post("/logout")
            self.locust.username = None
            # go to UnauthenticatedTasks
            self.interrupt()


class WebsiteUser(HttpLocust):
    task_set = AllTasks
    min_wait = 1000
    max_wait = 10000
