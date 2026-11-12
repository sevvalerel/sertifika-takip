from django.shortcuts import render
from django.utils import timezone

from certificates.models import Certificate


def certificate_list(request):
    # "Bugün" bir kez alınır: aynı sayfadaki tüm satırlar aynı tarihe göre hesaplanır.
    today = timezone.localdate()
    rows = [
        {
            "certificate": cert,
            "days_remaining": cert.days_remaining(today),
            "status": cert.status(today),
            "status_label": cert.status_label(today),
        }
        for cert in Certificate.objects.all()  # Meta.ordering: bitiş tarihi, alan adı
    ]
    return render(
        request,
        "certificates/certificate_list.html",
        {"rows": rows, "today": today},
    )
