import asyncio
import os
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from core.utils.caching_utils import cache_function


class TestCacheFunction(TestCase):
    @patch.dict(os.environ, {"CACHE_FUNCTION_ENABLED_PYTEST": "true"})
    def test_cache_function_sync(self):
        cache.clear()
        call_counter = {"calls": 0}

        @cache_function(timeout=60)
        def compute(value):
            call_counter["calls"] += 1
            return f"value={value};calls={call_counter['calls']}"

        first = compute(123)
        second = compute(123)

        self.assertEqual(first, second)
        self.assertEqual(call_counter["calls"], 1)

    @patch.dict(os.environ, {"CACHE_FUNCTION_ENABLED_PYTEST": "true"})
    def test_cache_function_sync_ignores_self_for_methods(self):

        cache.clear()
        call_counter = {"calls": 0}

        class Dummy:
            @cache_function(timeout=60, ignore_first_arg=True)
            def compute(self, value):
                call_counter["calls"] += 1
                return f"value={value};calls={call_counter['calls']}"

        first = Dummy().compute(123)
        second = Dummy().compute(123)

        self.assertEqual(first, second)
        self.assertEqual(call_counter["calls"], 1)

    @patch.dict(os.environ, {"CACHE_FUNCTION_ENABLED_PYTEST": "true"})
    def test_cache_function_async(self):
        cache.clear()
        call_counter = {"calls": 0}

        @cache_function(timeout=60)
        async def compute(value):
            call_counter["calls"] += 1
            return f"value={value};calls={call_counter['calls']}"

        async def run_test():
            first = await compute(123)
            second = await compute(123)

            self.assertEqual(first, second)
            self.assertEqual(call_counter["calls"], 1)

        asyncio.run(run_test())
