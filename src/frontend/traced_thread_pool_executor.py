# Copyright 2023 Google LLC
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

"""Enable tracing with a ThreadPoolExecutor"""

from concurrent.futures import ThreadPoolExecutor
from opentelemetry import context as otel_context

class TracedThreadPoolExecutor(ThreadPoolExecutor):
    """Implementation of :class:`ThreadPoolExecutor` that will pass context into sub tasks."""

    def __init__(self, tracer, *args, **kwargs):
        """Initialize TracedThreadPoolExecutor"""
        self.tracer = tracer
        super().__init__(*args, **kwargs)

    def with_otel_context(self, context, function):
        """Attach context"""
        otel_context.attach(context)
        return function()

    # pylint: disable-msg=arguments-differ
    def submit(self, function, *args, **kwargs):
        """Submit a new task to the thread pool."""

        # get the current otel context
        context = otel_context.get_current()
        if context:
            return super().submit(
                lambda: self.with_otel_context(
                    context, lambda: function(*args, **kwargs)
                ),
            )

        return super().submit(lambda: function(*args, **kwargs))
