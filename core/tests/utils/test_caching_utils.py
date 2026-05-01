import os
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from core.utils.caching_utils import cache_function


class TestCacheFunction(TestCase):
    @patch.dict(os.environ, {"CACHE_FUNCTION_ENABLED_PYTEST": "true"})
    def test_cache_function_ignores_self_for_methods(self):
        
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
