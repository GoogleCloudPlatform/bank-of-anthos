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
"""
Exercises the frontend endpoints for the system
"""


import json
import logging
from string import ascii_letters, digits
from random import randint, random, choice

from locust import HttpUser, TaskSet, SequentialTaskSet, task, between

MASTER_PASSWORD = "password"

TRANSACTION_ACCT_LIST = [str(randint(1111100000, 1111199999)) for _ in range(50)]

def signup_helper(locust, username):
    """
    create a new user account in the system
    succeeds if token was returned
    """
    userdata = {"username":username,
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
                "ssn":"111-22-3333"}
    with locust.client.post("/signup", data=userdata, catch_response=True) as response:
        for r_hist in response.history:
            if r_hist.cookies.get('token') is not None:
                response.success()
                logging.debug("created user = %s", username)
                return True

        response.failure("login failed")
        return False

def generate_username():
    """
    generates random 15 character
    alphanumeric username
    """
    return ''.join(choice(ascii_letters + digits) for _ in range(15))

class AllTasks(SequentialTaskSet):
    """
    wrapper for UnauthenticatedTasks and AuthenticatedTasks sets
    """
    @task
    class UnauthenticatedTasks(TaskSet):
        """
        set of tasks to run before obtaining an auth token
        """
        @task(5)
        def view_login(self):
            """
            load the /login page
            fails if already logged on (redirects to /home)
            """
            with self.client.get("/login", catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.status_code > 200 and r_hist.status_code < 400:
                        response.failure("Logged on: Got redirect to /home")

        @task(5)
        def view_signup(self):
            """
            load the /signup page
            fails if not logged on (redirects to /home)
            """
            with self.client.get("/signup", catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.status_code > 200 and r_hist.status_code < 400:
                        response.failure("Logged on: Got redirect to /home")

        @task(1)
        def signup(self):
            """
            sends POST request to /signup to create a new user
            on success, exits UnauthenticatedTasks
            """
            # sign up
            new_username = generate_username()
            success = signup_helper(self, new_username)
            if success:
                # go to AuthenticatedTasks
                self.user.username = new_username
                self.interrupt()

    @task
    class AuthenticatedTasks(TaskSet):
        """
        set of tasks to run after obtaining an auth token
        """
        def on_start(self):
            """
            on start, deposit a large balance into each account
            to ensure all payments are covered
            """
            self.deposit(1000000)

        @task(10)
        def view_index(self):
            """
            load the / page
            fails if not logged on (redirects to /login)
            """
            with self.client.get("/", catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.status_code > 200 and r_hist.status_code < 400:
                        response.failure("Not logged on: Got redirect to /login")

        @task(10)
        def view_home(self):
            """
            load the /home page (identical to /)
            fails if not logged on (redirects to /login)
            """
            with self.client.get("/home", catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.status_code > 200 and r_hist.status_code < 400:
                        response.failure("Not logged on: Got redirect to /login")

        @task(5)
        def payment(self, amount=None):
            """
            POST to /payment, sending money to other account
            """
            if amount is None:
                amount = random() * 1000
            transaction = {"account_num": choice(TRANSACTION_ACCT_LIST),
                           "amount": amount,
                           "uuid": generate_username()}
            with self.client.post("/payment",
                                  data=transaction,
                                  catch_response=True) as response:
                if response.url is None or "failed" in response.url:
                    response.failure("payment failed")

        @task(5)
        def deposit(self, amount=None):
            """
            POST to /deposit, depositing external money into account
            """
            if amount is None:
                amount = random() * 1000
            acct_info = {"account_num": choice(TRANSACTION_ACCT_LIST),
                         "routing_num":"111111111"}
            transaction = {"account": json.dumps(acct_info),
                           "amount": amount,
                           "uuid": generate_username()}
            with self.client.post("/deposit",
                                  data=transaction,
                                  catch_response=True) as response:
                if response.url is None or "failed" in response.url:
                    response.failure("deposit failed")

        @task(5)
        def login(self):
            """
            sends POST request to /login with stored credentials
            succeeds if a token was returned
            """
            with self.client.post("/login", {"username":self.user.username,
                                             "password":MASTER_PASSWORD},
                                  catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.cookies.get('token') is not None:
                        response.success()
                        return
                response.failure("login failed")

        @task(1)
        def logout(self):
            """
            sends a /logout POST request
            fails if not logged in
            exits AuthenticatedTasks
            """
            with self.client.post("/logout", catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.status_code > 200 and r_hist.status_code < 400:
                        response.success()
                        self.user.username = None
                        # go to UnauthenticatedTasks
                        self.interrupt()


class WebsiteUser(HttpUser):
    """
    Locust class to simulate HTTP users
    """
    tasks = [AllTasks]
    wait_time = between(1, 1)
