# Copyright 2026 Google LLC
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

"""Tests for frontend transaction submission responses."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend import create_app  # pylint: disable=wrong-import-position,no-name-in-module


class _FakeResponse:
    """Minimal requests response test double."""

    def __init__(self, status_code=200, json_data=None, text="", ok=True):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.ok = ok

    def json(self):
        """Return configured JSON data."""
        return self._json_data

    def raise_for_status(self):
        """Raise an HTTP error for failed status codes."""
        if self.status_code >= 400:
            raise HTTPError(self.text)


class TestFrontend(unittest.TestCase):
    """Test cases for frontend routes."""

    def setUp(self):
        """Setup Flask test client with mocked dependencies."""
        self.env_patcher = patch.dict(
            os.environ,
            {
                "TRANSACTIONS_API_ADDR": "transactions",
                "USERSERVICE_API_ADDR": "userservice",
                "BALANCES_API_ADDR": "balances",
                "HISTORY_API_ADDR": "history",
                "CONTACTS_API_ADDR": "contacts",
                "PUB_KEY_PATH": "public-key",
                "LOCAL_ROUTING_NUM": "883745000",
                "ENABLE_TRACING": "false",
                "METADATA_SERVER": "metadata",
            },
        )
        self.env_patcher.start()
        self.open_patcher = patch("frontend.open", mock_open(read_data="public"), create=True)
        self.open_patcher.start()
        self.get_patcher = patch("frontend.requests.get", side_effect=self._fake_get)
        self.get_patcher.start()
        self.api_get_patcher = patch("api_call.get", side_effect=self._fake_get)
        self.api_get_patcher.start()
        self.jwt_patcher = patch("frontend.jwt.decode", return_value={
            "acct": "1234567890",
            "user": "testuser",
            "name": "Test User",
        })
        self.jwt_patcher.start()

        self.flask_app = create_app()
        self.flask_app.config["TESTING"] = True
        self.test_app = self.flask_app.test_client()
        self.test_app.set_cookie("token", "valid-token")

    def tearDown(self):
        """Stop patchers."""
        self.jwt_patcher.stop()
        self.api_get_patcher.stop()
        self.get_patcher.stop()
        self.open_patcher.stop()
        self.env_patcher.stop()

    def test_payment_failure_returns_400_status_code(self):
        """Payment errors should not redirect to a 200 home response."""
        with patch(
            "frontend.requests.post",
            return_value=_FakeResponse(400, text="invalid transaction"),
        ):
            response = self.test_app.post(
                "/payment",
                data={
                    "account_num": "2345678901",
                    "amount": "-1000",
                    "uuid": "payment-uuid",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Payment failed: invalid transaction", response.data)

    def test_payment_backend_unavailable_returns_503_status_code(self):
        """Payment request transport errors should expose service failure."""
        with patch(
            "frontend.requests.post",
            side_effect=RequestsConnectionError("unavailable"),
        ):
            response = self.test_app.post(
                "/payment",
                data={
                    "account_num": "2345678901",
                    "amount": "10",
                    "uuid": "payment-uuid",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn(b"Payment failed", response.data)

    def test_deposit_failure_returns_400_status_code(self):
        """Deposit errors should not redirect to a 200 home response."""
        with patch(
            "frontend.requests.post",
            return_value=_FakeResponse(400, text="invalid deposit"),
        ):
            response = self.test_app.post(
                "/deposit",
                data={
                    "account": '{"account_num":"2345678901","routing_num":"123456789"}',
                    "amount": "-1000",
                    "uuid": "deposit-uuid",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Deposit failed: invalid deposit", response.data)

    @staticmethod
    def _fake_get(url, **_kwargs):
        if "/balances/" in url:
            return _FakeResponse(json_data=100000)
        if "/transactions/" in url:
            return _FakeResponse(json_data=[])
        if "/contacts/" in url:
            return _FakeResponse(json_data=[])
        return _FakeResponse(ok=False)


if __name__ == "__main__":
    unittest.main()
