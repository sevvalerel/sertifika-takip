from django.db import models
from django.utils import timezone

from certificates import status as cert_status


class Certificate(models.Model):
    domain = models.CharField("alan adı", max_length=253, unique=True)
    customer_name = models.CharField("müşteri adı", max_length=200)
    expiry_date = models.DateField("bitiş tarihi")

    class Meta:
        ordering = ["expiry_date", "domain"]
        verbose_name = "sertifika"
        verbose_name_plural = "sertifikalar"

    def __str__(self):
        return self.domain

    def _normalize_domain(self):
        if self.domain:
            self.domain = self.domain.strip().lower()

    def clean(self):
        # Admin formu tekillik kontrolünü clean()'den SONRA yapar. Burada
        # küçük harfe çevirince "Example.com" tekrarı form hatası olarak yakalanır.
        self._normalize_domain()

    def save(self, *args, **kwargs):
        # objects.create() gibi clean() çağrılmayan yollar için de normalize et.
        self._normalize_domain()
        super().save(*args, **kwargs)

    def days_remaining(self, today=None):
        return cert_status.days_remaining(self.expiry_date, today or timezone.localdate())

    def status(self, today=None):
        return cert_status.get_status(self.expiry_date, today or timezone.localdate())

    def status_label(self, today=None):
        return cert_status.STATUS_LABELS[self.status(today)]
