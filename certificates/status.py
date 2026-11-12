"""Sertifika durum hesabı.

Saf Python: Django'ya ve veritabanına bağlı değildir. "Bugün" her zaman
dışarıdan verilir, böylece testler sabit bir tarihle çalışabilir.

Kural (bkz. README > Varsayımlar):
    kalan < 0                        -> süresi dolmuş
    0 <= kalan <= EXPIRING_SOON_DAYS -> yakında dolacak
    kalan > EXPIRING_SOON_DAYS       -> geçerli
"""

EXPIRING_SOON_DAYS = 30

EXPIRED = "expired"
EXPIRING_SOON = "expiring_soon"
VALID = "valid"

STATUS_LABELS = {
    EXPIRED: "Süresi dolmuş",
    EXPIRING_SOON: "Yakında dolacak",
    VALID: "Geçerli",
}


def days_remaining(expiry_date, today):
    """Bitiş tarihine kalan gün. Süresi dolmuşsa negatiftir."""
    return (expiry_date - today).days


def get_status(expiry_date, today):
    days = days_remaining(expiry_date, today)
    if days < 0:
        return EXPIRED
    # Eşik burada okunur, varsayılan parametre olarak verilmez:
    # varsayılan değer tanım anında sabitlenir ve sonradan değiştirilemezdi.
    if days <= EXPIRING_SOON_DAYS:
        return EXPIRING_SOON
    return VALID
