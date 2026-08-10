#!/usr/bin/env python3
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

"""Fallback remediation job for fixable container vulnerabilities."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import yaml

SEVERITY_ORDER = {
    "MINIMAL": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
    "UNKNOWN": 0,
}


@dataclass
class FixableVulnerability:
    cve: str
    severity: str
    package_name: str
    fixed_version: str
    resource_url: str


@dataclass
class ImageConfig:
    name: str
    service: str
    dockerfile: str | None = None
    requirements_in: str | None = None
    pom: str | None = None


def load_image_map(path: Path) -> dict[str, ImageConfig]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    images: dict[str, ImageConfig] = {}
    for name, cfg in data["images"].items():
        images[name] = ImageConfig(name=name, **cfg)
    return images


def severity_at_least(severity: str, minimum: str) -> bool:
    return SEVERITY_ORDER.get(severity.upper(), 0) >= SEVERITY_ORDER.get(
        minimum.upper(), 3
    )


def run_cmd(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    return result.stdout.strip()


def run_gcloud(args: list[str]) -> str:
    return run_cmd(["gcloud", *args])


def list_latest_image_uri(project: str, location: str, repo: str, image: str) -> str | None:
    output = run_gcloud(
        [
            "artifacts",
            "docker",
            "images",
            "list",
            f"{location}-docker.pkg.dev/{project}/{repo}/{image}",
            "--include-tags",
            "--sort-by=~UPDATE_TIME",
            "--limit=1",
            "--format=value(IMAGE)",
        ]
    )
    return output or None


def list_fixable_vulnerabilities(
    image_uri: str, project: str, min_severity: str
) -> list[FixableVulnerability]:
    output = run_gcloud(
        [
            "artifacts",
            "docker",
            "images",
            "list-vulnerabilities",
            image_uri,
            "--project",
            project,
            "--format=json",
        ]
    )
    if not output:
        return []

    findings: list[FixableVulnerability] = []
    for item in json.loads(output):
        vuln = item.get("vulnerability", {})
        severity = vuln.get("effectiveSeverity") or vuln.get("severity") or "UNKNOWN"
        if not severity_at_least(severity, min_severity):
            continue

        fix_available = vuln.get("fixAvailable")
        if fix_available is False:
            continue
        if isinstance(fix_available, dict) and not fix_available:
            continue

        fixed_version = ""
        if isinstance(fix_available, dict):
            fixed_version = (
                fix_available.get("fixedVersion")
                or fix_available.get("fixedPackage")
                or ""
            )

        package_name = item.get("noteName", "").split("/")[-1]
        package_issues = vuln.get("packageIssue") or []
        if package_issues:
            package_name = package_issues[0].get("affectedPackage", package_name)

        cve = vuln.get("shortDescription") or item.get("noteName", "unknown")
        cve_match = re.search(r"CVE-\d{4}-\d+", cve)
        cve_id = cve_match.group(0) if cve_match else cve

        findings.append(
            FixableVulnerability(
                cve=cve_id,
                severity=severity,
                package_name=package_name,
                fixed_version=fixed_version,
                resource_url=image_uri,
            )
        )
    return findings


def resolve_latest_digest(image_ref: str) -> str | None:
    if "@sha256:" in image_ref:
        image_ref = image_ref.split("@", maxsplit=1)[0]
    output = run_gcloud(
        [
            "artifacts",
            "docker",
            "tags",
            "list",
            image_ref,
            "--format=json",
        ]
    )
    if not output:
        return None
    tags = json.loads(output)
    for tag in tags:
        version = tag.get("version")
        if version and version.startswith("sha256:"):
            return version.split(":", maxsplit=1)[1]
    return None


def update_dockerfile_base_digest(path: Path, new_digest: str) -> bool:
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(@sha256:)[a-f0-9]{64}",
        rf"\g<1>{new_digest}",
        content,
        count=1,
    )
    if count == 0:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def update_jib_base_digest(path: Path, new_digest: str) -> bool:
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(<image>[^<]+@sha256:)[a-f0-9]{64}(</image>)",
        rf"\g<1>{new_digest}\g<2>",
        content,
        count=1,
    )
    if count == 0:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def extract_base_image_ref(path: Path) -> str | None:
    content = path.read_text(encoding="utf-8")
    if path.name == "Dockerfile":
        match = re.search(r"^FROM\s+(\S+)", content, re.MULTILINE)
        return match.group(1) if match else None
    match = re.search(r"<image>([^<]+)</image>", content)
    return match.group(1) if match else None


def github_request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    response = requests.request(method, url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response


def load_github_token(project: str, secret_id: str) -> str:
    output = run_gcloud(
        [
            "secrets",
            "versions",
            "access",
            "latest",
            "--secret",
            secret_id,
            "--project",
            project,
        ]
    )
    secret = json.loads(output)
    return secret["installation_token"]


def open_pr_exists(
    owner: str,
    repo: str,
    token: str,
    service: str,
    cve: str,
    target_branch: str,
) -> bool:
    query = quote(
        f"repo:{owner}/{repo} is:pr is:open label:security label:automated-remediation "
        f"{service} {cve} in:title base:{target_branch}"
    )
    response = github_request(
        "GET",
        f"https://api.github.com/search/issues?q={query}",
        token,
    )
    return response.json().get("total_count", 0) > 0


def service_pr_open(
    owner: str, repo: str, token: str, service: str, target_branch: str
) -> bool:
    query = quote(
        f"repo:{owner}/{repo} is:pr is:open label:automated-remediation "
        f"{service} in:title base:{target_branch}"
    )
    response = github_request(
        "GET",
        f"https://api.github.com/search/issues?q={query}",
        token,
    )
    return response.json().get("total_count", 0) > 0


def create_remediation_pr(
    owner: str,
    repo: str,
    token: str,
    target_branch: str,
    service: str,
    cves: list[FixableVulnerability],
    changed_files: list[str],
    workspace: Path,
    project: str,
) -> None:
    branch = f"security-remediation/{service}-{int(time.time())}"
    cve_ids = sorted({item.cve for item in cves})
    title = f"security({service}): remediate {', '.join(cve_ids[:3])}"

    run_cmd(["git", "fetch", "origin", target_branch], cwd=workspace)
    run_cmd(["git", "checkout", "-B", branch, f"origin/{target_branch}"], cwd=workspace)
    run_cmd(["git", "add", *changed_files], cwd=workspace)
    run_cmd(
        [
            "git",
            "-c",
            "user.name=Security Remediation Bot",
            "-c",
            f"user.email=security-remediation@{project}.iam.gserviceaccount.com",
            "commit",
            "-m",
            title,
        ],
        cwd=workspace,
    )
    run_cmd(["git", "push", "origin", branch], cwd=workspace)

    body_lines = [
        "## Security remediation",
        "",
        f"Service: `{service}`",
        f"Target branch: `{target_branch}`",
        "",
        "| CVE | Severity | Package | Fixed version |",
        "| --- | --- | --- | --- |",
    ]
    for item in cves:
        body_lines.append(
            f"| {item.cve} | {item.severity} | {item.package_name} | "
            f"{item.fixed_version or 'see scan'} |"
        )
    body_lines.extend(
        [
            "",
            "Automated by the fallback remediation Cloud Build job.",
            "Please review and merge manually; auto-merge is disabled.",
        ]
    )

    pull = github_request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        token,
        {
            "title": title,
            "head": branch,
            "base": target_branch,
            "body": "\n".join(body_lines),
        },
    ).json()

    github_request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pull['number']}/labels",
        token,
        {"labels": ["security", "automated-remediation"]},
    )


def remediate_image(
    image_cfg: ImageConfig,
    project: str,
    location: str,
    repo: str,
    min_severity: str,
    owner: str,
    repo_name: str,
    token: str,
    target_branch: str,
    workspace: Path,
    dry_run: bool,
) -> None:
    image_uri = list_latest_image_uri(project, location, repo, image_cfg.name)
    if not image_uri:
        print(f"No published image found for {image_cfg.name}; skipping")
        return

    findings = list_fixable_vulnerabilities(image_uri, project, min_severity)
    if not findings:
        print(f"No fixable {min_severity}+ vulnerabilities for {image_cfg.name}")
        return

    if not dry_run and service_pr_open(owner, repo_name, token, image_cfg.service, target_branch):
        print(f"Open remediation PR already exists for {image_cfg.service}; skipping")
        return

    actionable = findings
    if not dry_run:
        actionable = [
            item
            for item in findings
            if not open_pr_exists(
                owner, repo_name, token, image_cfg.service, item.cve, target_branch
            )
        ]
    if not actionable:
        print(f"All findings for {image_cfg.name} already have open PRs")
        return

    changed_files: list[str] = []
    if image_cfg.dockerfile:
        dockerfile = workspace / image_cfg.dockerfile
        base_ref = extract_base_image_ref(dockerfile)
        if base_ref:
            new_digest = resolve_latest_digest(base_ref.split("@", maxsplit=1)[0])
            if new_digest and update_dockerfile_base_digest(dockerfile, new_digest):
                changed_files.append(image_cfg.dockerfile)
    elif image_cfg.pom:
        pom = workspace / image_cfg.pom
        base_ref = extract_base_image_ref(pom)
        if base_ref:
            new_digest = resolve_latest_digest(base_ref.split("@", maxsplit=1)[0])
            if new_digest and update_jib_base_digest(pom, new_digest):
                changed_files.append(image_cfg.pom)

    if not changed_files:
        print(f"Unable to derive source updates for {image_cfg.name}")
        return

    if dry_run:
        print(f"[dry-run] Would open PR for {image_cfg.service}: {changed_files}")
        return

    create_remediation_pr(
        owner,
        repo_name,
        token,
        target_branch,
        image_cfg.service,
        actionable,
        changed_files,
        workspace,
        project,
    )
    print(f"Opened remediation PR for {image_cfg.service}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=os.environ.get("PROJECT_ID"))
    parser.add_argument("--location", default=os.environ.get("LOCATION", "us-central1"))
    parser.add_argument(
        "--repository", default=os.environ.get("ARTIFACT_REPO", "bank-of-anthos")
    )
    parser.add_argument("--min-severity", default=os.environ.get("MIN_SEVERITY", "HIGH"))
    parser.add_argument(
        "--target-branch", default=os.environ.get("TARGET_BRANCH", "cursor-test")
    )
    parser.add_argument("--github-owner", default=os.environ.get("GITHUB_REPO_OWNER"))
    parser.add_argument("--github-repo", default=os.environ.get("GITHUB_REPO_NAME"))
    parser.add_argument("--github-secret", default=os.environ.get("GITHUB_SECRET"))
    parser.add_argument(
        "--image-map", default=str(Path(__file__).with_name("image-map.yaml"))
    )
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.project or not args.github_owner or not args.github_repo:
        print(
            "PROJECT_ID, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME are required",
            file=sys.stderr,
        )
        return 1

    workspace = Path(args.workspace)
    image_map = load_image_map(Path(args.image_map))

    token = ""
    if not args.dry_run:
        if not args.github_secret:
            print("GITHUB_SECRET is required unless --dry-run is set", file=sys.stderr)
            return 1
        token = load_github_token(args.project, args.github_secret)

    for image_cfg in image_map.values():
        remediate_image(
            image_cfg,
            args.project,
            args.location,
            args.repository,
            args.min_severity,
            args.github_owner,
            args.github_repo,
            token,
            args.target_branch,
            workspace,
            args.dry_run,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
