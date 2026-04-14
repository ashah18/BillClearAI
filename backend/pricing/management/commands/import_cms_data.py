"""
Management command to import CMS Physician Fee Schedule data from the three
official CMS data files stored in backend/pricing/data/.

Files expected in pricing/data/:
    indicators2026-03-18-2026.csv   — RVU file (~31,000 rows)
    localities2026-01-01-2026.csv   — GPCI file (110 rows)
    ZIP5_APR2026.csv                — ZIP crosswalk (~43,000 rows, actually an XLSX)

Usage:
    python manage.py import_cms_data

The command clears old rows before importing (idempotent).
"""

import csv
import io
import os
import shutil
import tempfile
import logging

from django.core.management.base import BaseCommand, CommandError

from pricing.models import LocalityGPCI, ProcedureRVU, ZipToLocality

logger = logging.getLogger(__name__)

# Absolute path to the data directory next to this file's app
DATA_DIR = os.path.join(
    os.path.dirname(__file__),  # commands/
    "..", "..",                 # pricing/
    "data",
)

INDICATORS_FILE = os.path.join(DATA_DIR, "indicators2026-03-18-2026.csv")
LOCALITIES_FILE = os.path.join(DATA_DIR, "localities2026-01-01-2026.csv")
ZIP5_FILE = os.path.join(DATA_DIR, "ZIP5_APR2026.csv")

# Import only the non-QP conversion factor to avoid duplicate (hcpc, modifier, year) rows
NON_QP_CONV_FACT = "33.4009"

# Proc_stat values worth storing (A=Active, B=Bundled, R=Restricted, T=Injection, X=Excluded)
KEEP_PROC_STATS = {"A", "B", "R", "T", "X"}

# Batch size for bulk_create
BATCH_SIZE = 500


def _is_xlsx(path: str) -> bool:
    """Detect XLSX by magic bytes (PK zip header), regardless of file extension."""
    with open(path, "rb") as fh:
        return fh.read(2) == b"PK"


def _open_xlsx_as_rows(path: str):
    """
    Load an XLSX file (possibly misnamed as .csv) and yield header + data rows.
    Returns (header_list, row_iterator).
    """
    try:
        import openpyxl
    except ImportError:
        raise CommandError(
            "openpyxl is required to read the ZIP5 XLSX file. "
            "Run: pip install openpyxl"
        )

    # openpyxl refuses to open files without an xlsx/xlsm extension;
    # copy to a temp file with the right extension.
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    shutil.copy2(path, tmp.name)
    try:
        wb = openpyxl.load_workbook(tmp.name, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = [str(c).strip() if c is not None else "" for c in next(rows)]
        return header, rows
    finally:
        os.unlink(tmp.name)


class Command(BaseCommand):
    help = "Import CMS fee schedule data (RVUs, GPCIs, ZIP crosswalk) from pricing/data/"

    def handle(self, *args, **options):
        for path, label in [
            (INDICATORS_FILE, "indicators"),
            (LOCALITIES_FILE, "localities"),
            (ZIP5_FILE, "ZIP5"),
        ]:
            if not os.path.exists(path):
                raise CommandError(f"Missing data file: {path}")

        self._import_localities()
        self._import_indicators()
        self._import_zip5()

    # ── Localities (GPCIs) ────────────────────────────────────────────────────

    def _import_localities(self):
        self.stdout.write("Importing localities (GPCIs)…")
        LocalityGPCI.objects.all().delete()

        objects = []
        with open(LOCALITIES_FILE, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                year = int(row["year"])
                objects.append(
                    LocalityGPCI(
                        locality=row["locality"].strip(),
                        loc_description=row["loc_description"].strip(),
                        mac=row["mac"].strip(),
                        gpci_work=row["gpci_work"],
                        gpci_pe=row["gpci_pe"],
                        gpci_mp=row["gpci_mp"],
                        year=year,
                    )
                )

        LocalityGPCI.objects.bulk_create(objects, batch_size=BATCH_SIZE)
        self.stdout.write(
            self.style.SUCCESS(f"  → {len(objects)} locality rows imported.")
        )

    # ── Indicators (RVUs) ─────────────────────────────────────────────────────

    def _import_indicators(self):
        self.stdout.write("Importing procedure RVUs…")
        ProcedureRVU.objects.all().delete()

        objects = []
        skipped = 0

        with open(INDICATORS_FILE, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            seen = set()  # track (hcpc, modifier, year) to deduplicate

            for row in reader:
                conv_fact = row.get("conv_fact", "").strip()
                # Keep only the non-QP conversion factor to avoid duplicate rows
                if conv_fact != NON_QP_CONV_FACT:
                    skipped += 1
                    continue

                proc_stat = row.get("proc_stat", "").strip()
                if proc_stat not in KEEP_PROC_STATS:
                    skipped += 1
                    continue

                hcpc = row["hcpc"].strip()
                modifier = row["modifier"].strip()
                year = int(row["year"])
                key = (hcpc, modifier, year)
                if key in seen:
                    skipped += 1
                    continue
                seen.add(key)

                def _dec(val, default="0"):
                    v = (val or "").strip()
                    return v if v else default

                objects.append(
                    ProcedureRVU(
                        hcpc=hcpc,
                        modifier=modifier,
                        short_description=row.get("sdesc", "").strip()[:120],
                        proc_stat=proc_stat,
                        rvu_work=_dec(row.get("rvu_work")),
                        full_nfac_pe=_dec(row.get("full_nfac_pe")),
                        full_fac_pe=_dec(row.get("full_fac_pe")),
                        rvu_mp=_dec(row.get("rvu_mp")),
                        conv_fact=conv_fact,
                        pctc=row.get("pctc", "").strip()[:2],
                        global_period=row.get("global", "").strip()[:5],
                        year=year,
                    )
                )

                if len(objects) >= BATCH_SIZE:
                    ProcedureRVU.objects.bulk_create(objects, batch_size=BATCH_SIZE)
                    objects = []

        if objects:
            ProcedureRVU.objects.bulk_create(objects, batch_size=BATCH_SIZE)

        total = ProcedureRVU.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"  → {total} procedure RVU rows imported ({skipped} skipped)."
            )
        )

    # ── ZIP5 crosswalk ────────────────────────────────────────────────────────

    def _import_zip5(self):
        self.stdout.write("Importing ZIP-to-locality crosswalk…")
        ZipToLocality.objects.all().delete()

        objects = []
        skipped = 0

        if _is_xlsx(ZIP5_FILE):
            header, rows = _open_xlsx_as_rows(ZIP5_FILE)
            # Build column index map (case-insensitive, strip spaces)
            col = {h.upper().strip(): i for i, h in enumerate(header)}

            def _get(row, name):
                idx = col.get(name)
                return str(row[idx]).strip() if idx is not None and row[idx] is not None else ""

            for row in rows:
                zip_code = _get(row, "ZIP CODE").zfill(5)[:5]
                state = _get(row, "STATE")[:2]
                carrier = _get(row, "CARRIER").zfill(5)[:5]
                locality_code = _get(row, "LOCALITY").zfill(2)[:2]
                year_qtr = _get(row, "YEAR/QTR")
                try:
                    year = int(str(year_qtr)[:4])
                except (ValueError, TypeError):
                    year = 2026

                if not zip_code or not carrier or not locality_code:
                    skipped += 1
                    continue

                objects.append(
                    ZipToLocality(
                        zip_code=zip_code,
                        state=state,
                        carrier=carrier,
                        locality_code=locality_code,
                        year=year,
                    )
                )

                if len(objects) >= BATCH_SIZE:
                    ZipToLocality.objects.bulk_create(
                        objects, batch_size=BATCH_SIZE, ignore_conflicts=True
                    )
                    objects = []
        else:
            # Plain CSV fallback (if the file was actually converted)
            with open(ZIP5_FILE, newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    zip_code = str(row.get("ZIP CODE") or row.get("zip_code") or "").strip().zfill(5)[:5]
                    state = str(row.get("STATE") or row.get("state") or "").strip()[:2]
                    carrier = str(row.get("CARRIER") or row.get("carrier") or "").strip().zfill(5)[:5]
                    locality_code = str(row.get("LOCALITY") or row.get("locality_code") or "").strip().zfill(2)[:2]
                    year_qtr = str(row.get("YEAR/QTR") or "2026").strip()
                    try:
                        year = int(year_qtr[:4])
                    except ValueError:
                        year = 2026

                    if not zip_code or not carrier or not locality_code:
                        skipped += 1
                        continue

                    objects.append(
                        ZipToLocality(
                            zip_code=zip_code,
                            state=state,
                            carrier=carrier,
                            locality_code=locality_code,
                            year=year,
                        )
                    )

                    if len(objects) >= BATCH_SIZE:
                        ZipToLocality.objects.bulk_create(
                            objects, batch_size=BATCH_SIZE, ignore_conflicts=True
                        )
                        objects = []

        if objects:
            ZipToLocality.objects.bulk_create(
                objects, batch_size=BATCH_SIZE, ignore_conflicts=True
            )

        total = ZipToLocality.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"  → {total} ZIP rows imported ({skipped} skipped)."
            )
        )
