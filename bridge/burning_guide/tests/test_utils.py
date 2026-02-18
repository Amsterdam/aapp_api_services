import freezegun
from django.core.cache import cache

from bridge.burning_guide.utils import (
    cache_until_expiry_hour,
    seconds_until_next_expiry_hour,
)


class TestSecondsUntilNextExpiryHour:
    @freezegun.freeze_time("2024-06-15 03:00:00")
    def test_before_first_boundary(self):
        expiry_hours = [4, 10, 16, 22]
        seconds = seconds_until_next_expiry_hour(expiry_hours)
        assert seconds == 60 * 60  # 1 hour until 4:00

    @freezegun.freeze_time("2024-06-15 05:00:00")
    def test_between_boundaries(self):
        expiry_hours = [4, 10, 16, 22]
        seconds = seconds_until_next_expiry_hour(expiry_hours)
        assert seconds == 5 * 60 * 60  # 5 hours until 10:00

    @freezegun.freeze_time("2024-06-15 23:00:00")
    def test_after_last_boundary(self):
        expiry_hours = [4, 10, 16, 22]
        seconds = seconds_until_next_expiry_hour(expiry_hours)
        assert seconds == 5 * 60 * 60  # 5 hours until next day's 4:00


@freezegun.freeze_time("2024-06-15 02:59:30")
class TestCacheUntilExpiryHourDecorator:
    def setup_method(self, _):
        cache.clear()
        self.counter_1, self.counter_2 = 0, 10

    @cache_until_expiry_hour(expiry_hours=[4, 10, 16, 22])
    def sample_function_1(self, x):
        self.counter_1 += 1
        return self.counter_1

    @cache_until_expiry_hour(expiry_hours=[4, 10, 16, 22])
    def sample_function_2(self, x):
        self.counter_2 += 1
        return self.counter_2

    def test_simple_cache(self):
        for _i in range(5):
            result = self.sample_function_1("foobar")
            assert len(cache.keys("*")) == 1
            assert result == 1

    def test_no_cache_different_args(self):
        for _i in range(3):
            _i += 1
            result = self.sample_function_1("arg" + str(_i))
            assert len(cache.keys("*")) == _i
            assert result == _i

    def test_cache_multiple_functions_same_args(self):
        for _i in range(3):
            _i += 1
            result = self.sample_function_1("arg" + str(_i))
            assert len(cache.keys("*")) == _i
            assert result == _i

        for _i in range(3):
            _i += 1
            result = self.sample_function_2("arg" + str(_i))
            assert len(cache.keys("*")) == _i + 3
            assert result == _i + 10

    def test_no_cache_multiple_functions_different_args(self):
        for _i in range(3):
            _i += 1
            result = self.sample_function_1("arg" + str(_i))
            assert len(cache.keys("*")) == _i
            assert result == _i

        for _i in range(3):
            _i += 1
            result = self.sample_function_2("arg" + str(_i))
            assert len(cache.keys("*")) == _i + 3
            assert result == _i + 10

    def test_no_cache_short_timeout(self):
        @cache_until_expiry_hour(expiry_hours=[3, 4])  # Next boundary in 30 seconds
        def short_timeout_function(x):
            self.counter_1 += 1
            return self.counter_1

        for _i in range(3):
            result = short_timeout_function("foobar")
            assert len(cache.keys("*")) == 0  # Should not cache
            assert result == _i + 1
