"""
Management command to import CMS Physician Fee Schedule data into the database.

Usage — from CSV files:
    python manage.py import_cms_prices \
        --fee-schedule path/to/fee_schedule.csv \
        --zip-crosswalk path/to/zip_crosswalk.csv \
        [--year 2024] [--clear]

Usage — generate synthetic sample data for testing:
    python manage.py import_cms_prices --sample [--year 2024]

Fee schedule CSV columns:
    cpt_code, locality_id, locality_name, state, mac_name,
    non_facility_amount, facility_amount, year

ZIP crosswalk CSV columns:
    zip_code, state, locality_id
"""

import csv
import random
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from pricing.models import CMSLocality, CMSPriceEntry, ZipLocality


# ── Common CPT codes used in the sample dataset ───────────────────────────────
_SAMPLE_CPT_CODES = [
    # Office visits
    "99201", "99202", "99203", "99204", "99205",
    "99211", "99212", "99213", "99214", "99215",
    # Preventive
    "99381", "99382", "99383", "99384", "99385", "99386", "99387",
    "99391", "99392", "99393", "99394", "99395", "99396", "99397",
    # Emergency
    "99281", "99282", "99283", "99284", "99285",
    # Lab
    "80050", "80053", "80061", "82947", "84443", "85025", "85027",
    # Imaging
    "71046", "71048", "72148", "73721", "74177", "74178",
    # Common procedures
    "93000", "93005", "93010", "93040", "93042",
    "20610", "20605", "20600",
    "11721", "11730", "11740",
    "29515", "29540", "29580",
    "43239", "45378", "45380", "45385",
    "69210", "92002", "92004", "92012", "92014",
    "96372", "96374", "96375",
    "97010", "97012", "97016", "97018", "97022", "97024",
    "97110", "97112", "97116", "97530",
    "99051", "99060",
]

# ── Realistic CMS localities (state, locality_id, name, mac_name) ─────────────
_SAMPLE_LOCALITIES = [
    ("NY", "14", "Manhattan", "First Coast Service Options"),
    ("NY", "16", "Queens", "First Coast Service Options"),
    ("NY", "18", "Rest of New York", "First Coast Service Options"),
    ("CA", "26", "Los Angeles", "Noridian Healthcare Solutions"),
    ("CA", "28", "San Francisco", "Noridian Healthcare Solutions"),
    ("CA", "29", "Rest of California", "Noridian Healthcare Solutions"),
    ("TX", "45", "Dallas/Ft. Worth", "Novitas Solutions"),
    ("TX", "47", "Houston", "Novitas Solutions"),
    ("TX", "49", "Rest of Texas", "Novitas Solutions"),
    ("FL", "01", "Florida", "First Coast Service Options"),
    ("IL", "16", "Chicago/Suburban", "Wisconsin Physicians Service"),
    ("IL", "17", "Rest of Illinois", "Wisconsin Physicians Service"),
    ("PA", "12", "Philadelphia", "Novitas Solutions"),
    ("PA", "14", "Rest of Pennsylvania", "Novitas Solutions"),
    ("OH", "16", "Ohio", "CGS Administrators"),
    ("GA", "01", "Georgia", "CGS Administrators"),
    ("NC", "99", "North Carolina", "Palmetto GBA"),
    ("WA", "18", "Seattle", "Noridian Healthcare Solutions"),
    ("WA", "19", "Rest of Washington", "Noridian Healthcare Solutions"),
    ("AZ", "99", "Arizona", "Noridian Healthcare Solutions"),
]

# ZIP ranges by state for the sample dataset
_STATE_ZIP_PREFIXES = {
    "NY": ["100", "101", "102", "103", "104", "110", "111", "112", "113", "114"],
    "CA": ["900", "901", "902", "910", "911", "912", "940", "941", "942", "943"],
    "TX": ["750", "751", "752", "770", "771", "772", "780", "781", "782", "783"],
    "FL": ["320", "321", "330", "331", "332", "333", "334", "335", "336", "337"],
    "IL": ["600", "601", "602", "603", "604", "605", "606", "607", "608", "609"],
    "PA": ["190", "191", "192", "193", "150", "151", "152", "153", "154", "155"],
    "OH": ["430", "431", "432", "433", "440", "441", "442", "443", "444", "445"],
    "GA": ["300", "301", "302", "303", "304", "305", "306", "307", "308", "309"],
    "NC": ["270", "271", "272", "273", "274", "275", "276", "277", "278", "279"],
    "WA": ["980", "981", "982", "983", "984", "985", "986", "987", "988", "989"],
    "AZ": ["850", "851", "852", "853", "854", "855", "856", "857", "858", "859"],
}

# Locality ID to state mapping for ZIP assignment
_LOCALITY_STATE = {loc[1]: loc[0] for loc in _SAMPLE_LOCALITIES}

# Base non-facility prices for each CPT code (approximate 2024 Medicare amounts)
_BASE_PRICES = {
    "99201": 22.00, "99202": 46.00, "99203": 77.00, "99204": 116.00, "99205": 153.00,
    "99211": 18.00, "99212": 46.00, "99213": 78.00, "99214": 116.00, "99215": 148.00,
    "99381": 64.00, "99382": 67.00, "99383": 70.00, "99384": 73.00,
    "99385": 76.00, "99386": 80.00, "99387": 84.00,
    "99391": 59.00, "99392": 63.00, "99393": 66.00, "99394": 69.00,
    "99395": 71.00, "99396": 75.00, "99397": 79.00,
    "99281": 26.00, "99282": 55.00, "99283": 95.00, "99284": 148.00, "99285": 218.00,
    "80050": 12.00, "80053": 14.00, "80061": 19.00, "82947": 7.00,
    "84443": 23.00, "85025": 9.00, "85027": 8.00,
    "71046": 46.00, "71048": 55.00, "72148": 101.00, "73721": 97.00,
    "74177": 152.00, "74178": 173.00,
    "93000": 17.00, "93005": 11.00, "93010": 8.00, "93040": 12.00, "93042": 7.00,
    "20610": 73.00, "20605": 54.00, "20600": 37.00,
    "11721": 34.00, "11730": 45.00, "11740": 57.00,
    "29515": 69.00, "29540": 58.00, "29580": 63.00,
    "43239": 302.00, "45378": 224.00, "45380": 258.00, "45385": 286.00,
    "69210": 52.00, "92002": 71.00, "92004": 112.00, "92012": 57.00, "92014": 91.00,
    "96372": 23.00, "96374": 51.00, "96375": 29.00,
    "97010": 7.00, "97012": 8.00, "97016": 8.00, "97018": 7.00,
    "97022": 8.00, "97024": 7.00,
    "97110": 30.00, "97112": 30.00, "97116": 29.00, "97530": 32.00,
    "99051": 18.00, "99060": 40.00,
}

# Geographic cost-of-living multipliers per locality
_LOCALITY_MULTIPLIER = {
    "14": 1.38, "16": 1.28, "18": 1.04,   # NY
    "26": 1.27, "28": 1.31, "29": 1.08,   # CA
    "45": 1.05, "47": 1.07, "49": 0.95,   # TX
    "01": 1.03, "16": 1.10, "17": 0.97,   # FL, IL
    "12": 1.14, "14": 0.99,               # PA
    "16": 1.00, "01": 0.96, "99": 0.98,   # OH, GA, NC, AZ
    "18": 1.17, "19": 1.02,               # WA
}


class Command(BaseCommand):
    help = "Import CMS Physician Fee Schedule pricing data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fee-schedule",
            metavar="PATH",
            help="Path to the fee schedule CSV file",
        )
        parser.add_argument(
            "--zip-crosswalk",
            metavar="PATH",
            help="Path to the ZIP-to-locality crosswalk CSV file",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=2024,
            help="Fee schedule year (default: 2024)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing CMSPriceEntry and ZipLocality rows for --year before importing",
        )
        parser.add_argument(
            "--sample",
            action="store_true",
            help="Generate a synthetic sample dataset for testing (ignores --fee-schedule / --zip-crosswalk)",
        )

    def handle(self, *args, **options):
        year = options["year"]

        if options["sample"]:
            self._generate_sample(year)
            return

        if not options["fee_schedule"] and not options["zip_crosswalk"]:
            raise CommandError(
                "Provide --fee-schedule and/or --zip-crosswalk, or use --sample."
            )

        if options["clear"]:
            deleted_prices, _ = CMSPriceEntry.objects.filter(year=year).delete()
            deleted_zips, _ = ZipLocality.objects.all().delete()
            self.stdout.write(
                f"Cleared {deleted_prices} price entries and {deleted_zips} ZIP mappings."
            )

        if options["zip_crosswalk"]:
            self._import_zip_crosswalk(options["zip_crosswalk"])

        if options["fee_schedule"]:
            self._import_fee_schedule(options["fee_schedule"], year)

    # ── CSV importers ──────────────────────────────────────────────────────────

    def _import_zip_crosswalk(self, path: str):
        """
        Import ZIP-to-locality crosswalk CSV.
        Expected columns: zip_code, state, locality_id
        """
        created = updated = skipped = 0
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                zip_code = str(row.get("zip_code", "")).strip().zfill(5)[:5]
                state = str(row.get("state", "")).strip().upper()[:2]
                locality_id = str(row.get("locality_id", "")).strip()

                if not zip_code or not locality_id:
                    skipped += 1
                    continue

                try:
                    locality = CMSLocality.objects.get(locality_id=locality_id)
                except CMSLocality.DoesNotExist:
                    skipped += 1
                    continue

                _, was_created = ZipLocality.objects.update_or_create(
                    zip_code=zip_code,
                    defaults={"state": state, "locality": locality},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"ZIP crosswalk: {created} created, {updated} updated, {skipped} skipped."
            )
        )

    def _import_fee_schedule(self, path: str, year: int):
        """
        Import fee schedule CSV.
        Expected columns: cpt_code, locality_id, locality_name, state, mac_name,
                          non_facility_amount, facility_amount, year
        """
        locality_created = price_created = price_updated = skipped = 0

        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                cpt_code = str(row.get("cpt_code", "")).strip()
                locality_id = str(row.get("locality_id", "")).strip()
                locality_name = str(row.get("locality_name", "")).strip()
                state = str(row.get("state", "")).strip().upper()[:2]
                mac_name = str(row.get("mac_name", "")).strip()
                row_year = int(row["year"]) if row.get("year") else year

                try:
                    non_fac = Decimal(str(row.get("non_facility_amount", "") or "0"))
                except InvalidOperation:
                    skipped += 1
                    continue

                fac_raw = str(row.get("facility_amount", "") or "").strip()
                try:
                    fac = Decimal(fac_raw) if fac_raw else None
                except InvalidOperation:
                    fac = None

                if not cpt_code or not locality_id:
                    skipped += 1
                    continue

                locality, loc_created = CMSLocality.objects.update_or_create(
                    locality_id=locality_id,
                    defaults={"name": locality_name, "state": state, "mac_name": mac_name},
                )
                if loc_created:
                    locality_created += 1

                _, was_created = CMSPriceEntry.objects.update_or_create(
                    cpt_code=cpt_code,
                    locality=locality,
                    year=row_year,
                    defaults={"non_facility_amount": non_fac, "facility_amount": fac},
                )
                if was_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Fee schedule: {locality_created} localities created, "
                f"{price_created} price entries created, "
                f"{price_updated} updated, {skipped} skipped."
            )
        )

    # ── Sample data generator ──────────────────────────────────────────────────

    def _generate_sample(self, year: int):
        """
        Generate a realistic synthetic dataset for development/testing.
        Creates ~20 localities, ~500 ZIP codes, and prices for ~60 CPT codes.
        """
        random.seed(42)  # reproducible output

        # 1. Create localities
        loc_created = loc_updated = 0
        locality_objects = {}
        for state, loc_id, name, mac_name in _SAMPLE_LOCALITIES:
            locality, created = CMSLocality.objects.update_or_create(
                locality_id=f"{state}-{loc_id}",
                defaults={"name": name, "state": state, "mac_name": mac_name},
            )
            locality_objects[f"{state}-{loc_id}"] = locality
            if created:
                loc_created += 1
            else:
                loc_updated += 1

        self.stdout.write(f"Localities: {loc_created} created, {loc_updated} updated.")

        # 2. Create ZIP-to-locality mappings (~500 ZIPs)
        zip_created = zip_updated = 0
        for state, loc_id, _name, _mac in _SAMPLE_LOCALITIES:
            full_loc_id = f"{state}-{loc_id}"
            locality = locality_objects[full_loc_id]
            prefixes = _STATE_ZIP_PREFIXES.get(state, ["000"])
            # Use the first prefix for this state/locality combination
            prefix_idx = list(_STATE_ZIP_PREFIXES.keys()).index(state) if state in _STATE_ZIP_PREFIXES else 0
            prefix = prefixes[0]

            for suffix in range(1, 31):  # ~30 ZIPs per locality entry
                zip_code = f"{prefix}{suffix:02d}"[:5].ljust(5, "0")
                _, created = ZipLocality.objects.update_or_create(
                    zip_code=zip_code,
                    defaults={"state": state, "locality": locality},
                )
                if created:
                    zip_created += 1
                else:
                    zip_updated += 1

        self.stdout.write(f"ZIP mappings: {zip_created} created, {zip_updated} updated.")

        # 3. Create price entries for each CPT × locality
        price_created = price_updated = 0
        for full_loc_id, locality in locality_objects.items():
            state, loc_id = full_loc_id.split("-", 1)
            multiplier = _LOCALITY_MULTIPLIER.get(loc_id, 1.0)

            for cpt_code in _SAMPLE_CPT_CODES:
                base = _BASE_PRICES.get(cpt_code, 50.00)
                # Add small random variation (±5%) around the geographic multiplier
                jitter = random.uniform(0.95, 1.05)
                non_fac = Decimal(str(round(base * multiplier * jitter, 2)))
                fac = Decimal(str(round(float(non_fac) * 0.75, 2)))  # facility ≈ 75% of non-fac

                _, created = CMSPriceEntry.objects.update_or_create(
                    cpt_code=cpt_code,
                    locality=locality,
                    year=year,
                    defaults={"non_facility_amount": non_fac, "facility_amount": fac},
                )
                if created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(f"Price entries: {price_created} created, {price_updated} updated.")
        self.stdout.write(
            self.style.SUCCESS(
                f"Sample data loaded for {len(locality_objects)} localities, "
                f"{len(_SAMPLE_CPT_CODES)} CPT codes, year {year}."
            )
        )
