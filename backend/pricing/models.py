from django.db import models


class CPTPriceCache(models.Model):
    """
    Legacy cache for CPT code descriptions. Kept for backward compatibility.
    Superseded by ProcedureRVU for pricing calculations.
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


class ProcedureRVU(models.Model):
    """
    CMS Physician Fee Schedule RVU data per CPT/HCPCS code.

    Imported from: indicators2026-03-18-2026.csv (~31,000 rows).
    We import only rows where conv_fact = 33.4009 (non-QP) to avoid
    duplicates, and only proc_stat in A, B, R, T, X for meaningful codes.

    Status codes:
        A = Active (valid pricing under PFS)
        B = Bundled (included in payment for another code)
        R = Restricted (contractor-priced)
        T = Injections (add-on, priced with base code)
        X = Excluded (priced under separate fee schedule, e.g. CLFS for labs)
    """

    hcpc = models.CharField(max_length=10, db_index=True)
    modifier = models.CharField(max_length=2, blank=True, default="")
    short_description = models.CharField(max_length=120, blank=True, default="")
    proc_stat = models.CharField(max_length=1, blank=True, default="")
    rvu_work = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    full_nfac_pe = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    full_fac_pe = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    rvu_mp = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    conv_fact = models.DecimalField(max_digits=10, decimal_places=4, default=33.4009)
    pctc = models.CharField(max_length=2, blank=True, default="")
    global_period = models.CharField(max_length=5, blank=True, default="")
    year = models.IntegerField(default=2026)

    class Meta:
        unique_together = ("hcpc", "modifier", "year")
        indexes = [models.Index(fields=["hcpc", "year"])]
        verbose_name = "Procedure RVU"
        verbose_name_plural = "Procedure RVUs"

    def __str__(self):
        mod = f"/{self.modifier}" if self.modifier else ""
        return f"{self.hcpc}{mod} ({self.year}) — Work: {self.rvu_work}"


class LocalityGPCI(models.Model):
    """
    CMS Geographic Practice Cost Index (GPCI) values per Medicare locality.

    Imported from: localities2026-01-01-2026.csv (110 rows).
    The locality field is a 7-digit concatenation of the 5-digit MAC code
    and the 2-digit locality suffix (e.g., MAC "01112" + "05" = "0111205").

    GPCIs adjust the national RVU amounts for regional cost differences.
    """

    locality = models.CharField(max_length=7, db_index=True)
    loc_description = models.CharField(max_length=250, blank=True, default="")
    mac = models.CharField(max_length=5, blank=True, default="")
    gpci_work = models.DecimalField(max_digits=6, decimal_places=3, default=1)
    gpci_pe = models.DecimalField(max_digits=6, decimal_places=3, default=1)
    gpci_mp = models.DecimalField(max_digits=6, decimal_places=3, default=1)
    year = models.IntegerField(default=2026)

    class Meta:
        unique_together = ("locality", "year")
        verbose_name = "Locality GPCI"
        verbose_name_plural = "Locality GPCIs"

    def __str__(self):
        return f"{self.locality} — {self.loc_description} ({self.year})"


class ZipToLocality(models.Model):
    """
    Maps 5-digit ZIP codes to their CMS carrier + locality code.

    Imported from: ZIP5_APR2026.xlsx (~42,000 rows).
    To look up GPCIs: concatenate carrier (5 chars) + locality_code (2 chars)
    to form the 7-digit LocalityGPCI.locality key.

    Example: carrier="01112", locality_code="05" → LocalityGPCI.locality="0111205"
    """

    zip_code = models.CharField(max_length=5, db_index=True)
    state = models.CharField(max_length=2, blank=True, default="")
    carrier = models.CharField(max_length=5)
    locality_code = models.CharField(max_length=2)
    year = models.IntegerField(default=2026)

    class Meta:
        unique_together = ("zip_code", "year")
        verbose_name = "ZIP-to-Locality"
        verbose_name_plural = "ZIP-to-Locality Mappings"

    def __str__(self):
        return f"{self.zip_code} → {self.carrier}{self.locality_code} ({self.year})"
