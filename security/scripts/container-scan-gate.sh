#!/usr/bin/env bash
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

set -euo pipefail

ARTIFACTS_FILE="${1:-/workspace/artifacts.json}"
MIN_SEVERITY="${MIN_SEVERITY:-HIGH}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-600}"
POLL_SECONDS="${POLL_SECONDS:-15}"

if [[ ! -f "${ARTIFACTS_FILE}" ]]; then
  echo "Artifacts file not found: ${ARTIFACTS_FILE}"
  exit 1
fi

severity_rank() {
  case "$1" in
    CRITICAL) echo 4 ;;
    HIGH) echo 3 ;;
    MEDIUM) echo 2 ;;
    LOW) echo 1 ;;
    *) echo 0 ;;
  esac
}

min_rank="$(severity_rank "${MIN_SEVERITY}")"

mapfile -t images < <(python3 - <<'PY' "${ARTIFACTS_FILE}"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

for build in data.get("builds", []):
    tag = build.get("tag") or build.get("imageName")
    if tag:
        print(tag)
PY
)

if [[ "${#images[@]}" -eq 0 ]]; then
  echo "No built images found in ${ARTIFACTS_FILE}"
  exit 1
fi

wait_for_scan() {
  local image_uri="$1"
  local elapsed=0
  while (( elapsed < MAX_WAIT_SECONDS )); do
    if gcloud artifacts docker images list-vulnerabilities "${image_uri}" \
      --project="${PROJECT_ID}" \
      --format=json >/tmp/scan.json 2>/dev/null; then
      if [[ -s /tmp/scan.json ]]; then
        return 0
      fi
      if grep -q '^\[\]$' /tmp/scan.json; then
        return 0
      fi
    fi
    sleep "${POLL_SECONDS}"
    elapsed=$((elapsed + POLL_SECONDS))
  done
  echo "Timed out waiting for scan results for ${image_uri}"
  exit 1
}

check_fixable_vulnerabilities() {
  local image_uri="$1"
  local findings
  findings="$(gcloud artifacts docker images list-vulnerabilities "${image_uri}" \
    --project="${PROJECT_ID}" \
    --format=json)"

  python3 - <<'PY' "${findings}" "${MIN_SEVERITY}"
import json
import sys

findings = json.loads(sys.argv[1])
min_severity = sys.argv[2]
order = {"MINIMAL": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 0}
min_rank = order.get(min_severity.upper(), 3)

violations = []
for item in findings:
    vuln = item.get("vulnerability", {})
    severity = (vuln.get("effectiveSeverity") or vuln.get("severity") or "UNKNOWN").upper()
    if order.get(severity, 0) < min_rank:
        continue
    fix_available = vuln.get("fixAvailable")
    if fix_available is False:
        continue
    if isinstance(fix_available, dict) and not fix_available:
        continue
    cve = vuln.get("shortDescription") or item.get("noteName", "unknown")
    violations.append(f"{cve} ({severity})")

if violations:
    print("Fixable vulnerabilities remain after build:")
    for line in violations:
        print(f"  - {line}")
    raise SystemExit(1)
PY
}

for image_uri in "${images[@]}"; do
  echo "Waiting for vulnerability scan on ${image_uri}"
  wait_for_scan "${image_uri}"
  echo "Checking fixable vulnerabilities for ${image_uri}"
  check_fixable_vulnerabilities "${image_uri}"
done

echo "Container scan gate passed"
