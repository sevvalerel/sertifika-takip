from datetime import UTC, date, datetime, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from certificates import status
from certificates.models import Certificate
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


class CertificateModelTests(TestCase):
    def test_domain_is_stripped_and_lowercased_on_save(self):
        cert = Certificate.objects.create(
            domain="  Example.COM ", customer_name="Acme", expiry_date=TODAY
        )
        cert.refresh_from_db()
        self.assertEqual(cert.domain, "example.com")

    def test_duplicate_with_different_case_fails_full_clean(self):
        Certificate.objects.create(
            domain="example.com", customer_name="Acme", expiry_date=TODAY
        )
        duplicate = Certificate(
            domain="EXAMPLE.com", customer_name="Baska", expiry_date=TODAY
        )
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn("domain", ctx.exception.message_dict)

    def test_duplicate_via_model_form_is_form_error(self):
        # Admin'in kullandığı yol: 500 yerine form hatası beklenir.
        Certificate.objects.create(
            domain="example.com", customer_name="Acme", expiry_date=TODAY
        )
        Form = modelform_factory(Certificate, fields="__all__")
        form = Form(
            data={
                "domain": "EXAMPLE.com",
                "customer_name": "Baska",
                "expiry_date": "2026-12-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("domain", form.errors)

    def test_editing_existing_record_does_not_clash_with_itself(self):
        # Tekillik kontrolü düzenlenen kaydın kendisini "tekrar" saymamalı.
        cert = Certificate.objects.create(
            domain="dun.com", customer_name="A", expiry_date=TODAY
        )
        Form = modelform_factory(Certificate, fields="__all__")
        form = Form(
            instance=cert,
            data={
                "domain": "DUN.com",
                "customer_name": "Ahmet",
                "expiry_date": "2026-11-12",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        cert.refresh_from_db()
        self.assertEqual(cert.domain, "dun.com")
        self.assertEqual(cert.customer_name, "Ahmet")
        self.assertEqual(Certificate.objects.count(), 1)

    def test_admin_count_uses_singular_noun(self):
        # Türkçede sayıdan sonra isim tekil kalır: "2 sertifika".
        for domain in ["a.com", "b.com"]:
            Certificate.objects.create(domain=domain, customer_name="Acme", expiry_date=TODAY)
        admin_user = User.objects.create_superuser("admin", password="x")
        self.client.force_login(admin_user)
        response = self.client.get("/admin/certificates/certificate/")
        # html=True: boşluk/satır sonu farkını yok sayar, paragraf içeriğini karşılaştırır.
        self.assertContains(response, '<p class="paginator">2 sertifika</p>', html=True)
        self.assertContains(response, "Sertifika Takip Yönetimi")

    def test_status_methods_use_given_today(self):
        cert = Certificate(domain="a.com", customer_name="Acme", expiry_date=in_days(30))
        self.assertEqual(cert.days_remaining(TODAY), 30)
        self.assertEqual(cert.status_label(TODAY), "Yakında dolacak")


# İstanbul'da 12 Kasım 2026 öğlen (UTC+3).
NOON_IN_ISTANBUL = datetime(2026, 11, 12, 9, 0, tzinfo=UTC)


@mock.patch("django.utils.timezone.now", return_value=NOON_IN_ISTANBUL)
class CertificateListViewTests(TestCase):
    def create(self, domain, days):
        return Certificate.objects.create(
            domain=domain, customer_name="Acme", expiry_date=in_days(days)
        )

    def get_rows(self):
        response = self.client.get(reverse("certificate_list"))
        self.assertEqual(response.status_code, 200)
        return response, response.context["rows"]

    def test_rows_sorted_by_expiry_with_days_and_status(self, _now):
        self.create("gecerli.com", 31)
        self.create("dolmus.com", -1)
        self.create("yakinda.com", 0)

        response, rows = self.get_rows()

        self.assertEqual(
            [(r["certificate"].domain, r["days_remaining"], r["status_label"]) for r in rows],
            [
                ("dolmus.com", -1, "Süresi dolmuş"),
                ("yakinda.com", 0, "Yakında dolacak"),
                ("gecerli.com", 31, "Geçerli"),
            ],
        )
        self.assertContains(response, "Süresi dolmuş")
        self.assertContains(response, "Yakında dolacak")
        self.assertContains(response, "Geçerli")
        # Admin'in kabul ettiği formatla aynı (gün/ay/yıl): 11/11/2026.
        self.assertContains(response, "11/11/2026")

    def test_same_expiry_date_sorted_by_domain(self, _now):
        self.create("b.com", 10)
        self.create("a.com", 10)

        _, rows = self.get_rows()

        self.assertEqual([r["certificate"].domain for r in rows], ["a.com", "b.com"])

    def test_empty_list_message(self, _now):
        response, rows = self.get_rows()

        self.assertEqual(rows, [])
        self.assertContains(response, "Henüz sertifika yok")

    def test_today_uses_istanbul_date_not_utc(self, now):
        # UTC'de hâlâ 12 Kasım 22:30, ama İstanbul'da 13 Kasım 01:30.
        now.return_value = datetime(2026, 11, 12, 22, 30, tzinfo=UTC)
        self.create("dun-doldu.com", 0)  # bitiş: 12 Kasım

        response, rows = self.get_rows()

        self.assertEqual(response.context["today"], date(2026, 11, 13))
        self.assertEqual(rows[0]["days_remaining"], -1)
        self.assertEqual(rows[0]["status_label"], "Süresi dolmuş")
