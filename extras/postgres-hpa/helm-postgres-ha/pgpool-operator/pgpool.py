# Copyright 2022 Google LLC
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

import asyncio
import datetime
import logging
import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

LOCK: asyncio.Lock

@kopf.on.startup()
async def startup(**_):
    """
    uses the running asyncio loop by default
    """
    global LOCK
    LOCK = asyncio.Lock()


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.WARNING
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 10 * 60


@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs):
    return datetime.datetime.utcnow().isoformat()


@kopf.on.login()
def login(**kwargs):
    global api

    conn = kopf.login_via_client(**kwargs)
    api = client.AppsV1Api()
    return conn


def replicas_changed(old, new, **_):
    new_replicas = new.get('spec', {}).get('replicas', 0) if new else 0
    old_replicas = old.get('spec', {}).get('replicas', 0) if old else 0
    return new_replicas != old_replicas



@kopf.on.update(kind="StatefulSet",
                when=replicas_changed,
                labels={
                    "app.kubernetes.io/component": "postgresql",
                    "app.kubernetes.io/instance": "accounts-db",
                })
def reconcile_backend_nodes(logger, namespace, new, **_):
    replicas = new.get('spec', {}).get('replicas', 0) if new else 0
    hosts = [
        f"{i}:accounts-db-postgresql-{i}.accounts-db-postgresql-headless:5432" \
        for i in range(replicas)
    ]

    def propagate_hostenv(envvar, hosts):
        if envvar.name == "PGPOOL_BACKEND_NODES":
            return {
                "name": "PGPOOL_BACKEND_NODES",
                "value": ",".join(hosts),
            }
        return envvar

    try:
        pgpool = api.read_namespaced_deployment(name="accounts-db-pgpool", namespace=namespace)
        for container in pgpool.spec.template.spec.containers:
            container.env = [propagate_hostenv(envvar, hosts) for envvar in container.env]

        api.patch_namespaced_deployment(
            name="accounts-db-pgpool",
            namespace=namespace,
            body=pgpool
        )
        logger.info("PGPool deployment updated")
    except ApiException as e:
        raise kopf.TemporaryError("Error when calling AppsV1Api: %s\n" % e, delay=60)
