# Copyright 2021 Google LLC
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

#!/bin/bash 

# uwsgi + flask startup script for the frontend. 
# startup command depends on SCHEME (http / https)

HTTPS="https"

if [ "$SCHEME" == "$HTTPS" ]; then 
    # start UWSGI with HTTPS, using the user-provided key pair 
    echo "Starting HTTPS frontend on port ${PORT}"
    uwsgi --ini /uwsgi-conf.ini --https :${PORT},/tls/public.crt,/tls/private.key
else
    # start UWSGI with plain http
    echo "Starting HTTP frontend ${PORT}"
    uwsgi --ini /uwsgi-conf.ini --http :${PORT}
fi