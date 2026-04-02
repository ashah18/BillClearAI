from django.db import models


class CPTPriceCache(models.Model):
    """
    Caches CPT code descriptions and national average prices to reduce
    repeated API lookups. Populated on-demand from CMS fee schedule data.
    """

    cpt_code = models.CharField(max_length=10, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    national_average = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CPT Price Cache"
        verbose_name_plural = "CPT Price Caches"

    def __str__(self):
        return f"{self.cpt_code} — ${self.national_average}"
