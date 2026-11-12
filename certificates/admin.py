from django.contrib import admin

from certificates.models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["domain", "customer_name", "expiry_date", "days_left", "status"]
    search_fields = ["domain", "customer_name"]
    list_filter = ["expiry_date"]

    @admin.display(description="kalan gün")
    def days_left(self, obj):
        return obj.days_remaining()

    @admin.display(description="durum")
    def status(self, obj):
        return obj.status_label()
