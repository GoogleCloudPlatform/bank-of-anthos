#!/usr/bin/env python3
"""Unit tests for security remediation helpers."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from remediate import (
    FixableVulnerability,
    list_fixable_vulnerabilities,
    open_pr_exists,
    severity_at_least,
    update_dockerfile_base_digest,
    update_jib_base_digest,
)


class RemediationTests(unittest.TestCase):
    def test_severity_at_least(self) -> None:
        self.assertTrue(severity_at_least("CRITICAL", "HIGH"))
        self.assertFalse(severity_at_least("MEDIUM", "HIGH"))

    def test_update_dockerfile_base_digest(self) -> None:
        path = Path("Dockerfile.test")
        path.write_text(
            "FROM python:3.14.3-slim@sha256:"
            "6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456\n",
            encoding="utf-8",
        )
        try:
            changed = update_dockerfile_base_digest(path, "a" * 64)
            self.assertTrue(changed)
            self.assertIn("a" * 64, path.read_text(encoding="utf-8"))
        finally:
            path.unlink(missing_ok=True)

    def test_update_jib_base_digest(self) -> None:
        path = Path("pom.test.xml")
        path.write_text(
            "<from><image>eclipse-temurin:17@sha256:"
            "e1506ba20f0cb2af6f23e24c7f8855b417f0b085708acd9b85344a884ba77767"
            "</image></from>\n",
            encoding="utf-8",
        )
        try:
            changed = update_jib_base_digest(path, "b" * 64)
            self.assertTrue(changed)
            self.assertIn("b" * 64, path.read_text(encoding="utf-8"))
        finally:
            path.unlink(missing_ok=True)

    @mock.patch("remediate.run_gcloud")
    def test_list_fixable_vulnerabilities_filters_non_fixable(
        self, mock_gcloud: mock.Mock
    ) -> None:
        mock_gcloud.return_value = json.dumps(
            [
                {
                    "noteName": "projects/test/notes/CVE-2024-1234",
                    "vulnerability": {
                        "effectiveSeverity": "HIGH",
                        "fixAvailable": {"fixedVersion": "1.2.3"},
                        "shortDescription": "CVE-2024-1234",
                        "packageIssue": [{"affectedPackage": "openssl"}],
                    },
                },
                {
                    "noteName": "projects/test/notes/CVE-2024-9999",
                    "vulnerability": {
                        "effectiveSeverity": "CRITICAL",
                        "fixAvailable": False,
                        "shortDescription": "CVE-2024-9999",
                    },
                },
            ]
        )
        findings = list_fixable_vulnerabilities("image@sha256:abc", "test", "HIGH")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].cve, "CVE-2024-1234")

    @mock.patch("remediate.github_request")
    def test_open_pr_exists(self, mock_request: mock.Mock) -> None:
        mock_request.return_value = mock.Mock(json=lambda: {"total_count": 1})
        self.assertTrue(
            open_pr_exists("owner", "repo", "token", "frontend", "CVE-2024-1", "cursor-test")
        )


if __name__ == "__main__":
    unittest.main()
