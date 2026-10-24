from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from cantusdata.models import Manuscript

MANIFESTS_CSV = "cantusdata.management.commands.import_data.MANIFESTS_CSV"


class ImportIIIFTestCase(TestCase):
    def run_import(self, rows: list[tuple[str, str]]) -> str:
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "manifests.csv"
            csv_path.write_text(
                "siglum,manifest_url\n"
                + "".join(f"{siglum},{url}\n" for siglum, url in rows),
                encoding="utf-8",
            )
            out = StringIO()
            with patch(MANIFESTS_CSV, csv_path):
                call_command("import_data", "iiif", stdout=out)
        return out.getvalue()

    def manifest(self, pk: int) -> str:
        return Manuscript.objects.get(pk=pk).manifest_url or ""

    def test_only_missing_manifests_are_filled(self) -> None:
        Manuscript.objects.create(id=1, siglum="A-1")
        Manuscript.objects.create(id=2, siglum="B-2", manifest_url="https://b/m")
        # Corrected by hand since the CSV was written, and mapped against it.
        Manuscript.objects.create(
            id=3,
            siglum="C-3",
            manifest_url="https://c/curated",
            public=True,
            is_mapped="MAPPED",
        )
        # Entered by hand; the CSV has never heard of it.
        Manuscript.objects.create(id=4, siglum="D-4", manifest_url="https://d/hand")
        Manuscript.objects.create(id=5, siglum="E-5")
        Manuscript.objects.create(id=6, siglum="E-5")

        output = self.run_import(
            [
                ("A-1", "https://a/m"),
                ("B-2", "https://b/m"),
                ("C-3", "http://c/stale "),
                ("Z-9", "https://z/m"),
                ("E-5", "https://e/m"),
            ]
        )

        self.assertEqual(self.manifest(1), "https://a/m")
        self.assertEqual(self.manifest(2), "https://b/m")
        self.assertEqual(self.manifest(3), "https://c/curated")
        self.assertEqual(self.manifest(4), "https://d/hand")
        # Two manuscripts share the siglum: neither is guessed at.
        self.assertEqual(self.manifest(5), "")
        self.assertEqual(self.manifest(6), "")
        self.assertIn(
            "Filled 1, unchanged 1, kept 1 that differ, 1 unmatched, 1 ambiguous.",
            output,
        )
        self.assertIn(
            "3 C-3 (public, mapped) keeps https://c/curated (CSV: http://c/stale)",
            output,
        )
        self.assertIn("No manuscript with siglum: Z-9", output)
        self.assertIn("Several manuscripts share siglum, skipped: E-5", output)
