from datetime import date, timedelta
from unittest import mock

from django.test import SimpleTestCase

from certificates import status
from certificates.status import (
    EXPIRED,
    EXPIRING_SOON,
    VALID,
    days_remaining,
    get_status,
)

TODAY = date(2026, 11, 12)


def in_days(n):
    return TODAY + timedelta(days=n)


class GetStatusTests(SimpleTestCase):
    """Üç durum sınıfı ve aralarındaki iki sınır (-1/0 ve 30/31)."""

    def test_expired_yesterday(self):
        self.assertEqual(get_status(in_days(-1), TODAY), EXPIRED)

    def test_expired_long_ago(self):
        self.assertEqual(get_status(in_days(-365), TODAY), EXPIRED)

    def test_expires_today_is_expiring_soon(self):
        # RFC 5280: bitiş anı geçerlilik süresine dahil.
        self.assertEqual(get_status(TODAY, TODAY), EXPIRING_SOON)

    def test_expires_tomorrow_is_expiring_soon(self):
        self.assertEqual(get_status(in_days(1), TODAY), EXPIRING_SOON)

    def test_threshold_day_is_expiring_soon(self):
        self.assertEqual(get_status(in_days(30), TODAY), EXPIRING_SOON)

    def test_day_after_threshold_is_valid(self):
        self.assertEqual(get_status(in_days(31), TODAY), VALID)

    def test_far_future_is_valid(self):
        self.assertEqual(get_status(in_days(365), TODAY), VALID)

    def test_threshold_constant_is_used(self):
        with mock.patch.object(status, "EXPIRING_SOON_DAYS", 14):
            self.assertEqual(get_status(in_days(14), TODAY), EXPIRING_SOON)
            self.assertEqual(get_status(in_days(15), TODAY), VALID)


class DaysRemainingTests(SimpleTestCase):
    def test_negative_when_expired(self):
        self.assertEqual(days_remaining(in_days(-5), TODAY), -5)

    def test_across_year_boundary(self):
        self.assertEqual(days_remaining(date(2027, 1, 1), date(2026, 12, 31)), 1)

    def test_leap_year(self):
        self.assertEqual(days_remaining(date(2028, 3, 1), date(2028, 2, 28)), 2)
