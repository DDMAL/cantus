from io import StringIO
from unittest.mock import patch
from urllib.error import URLError

from django.core.management import call_command
from django.test import TestCase

from cantusdata.management.commands.import_data import Command
from cantusdata.models import Chant, Folio, Manuscript, MEISubmission, NeumeExemplar
from cantusdata.test.core.fake_generators import create_fake_neume_exemplar

GENRES = "cantusdata.helpers.expandr.GenreExpander.load_genre_data"
COLUMNS = (
    "marginalia,sequence,cantus_id,feast,service,genre,mode,differentia,"
    "differentiae_database,finalis,incipit,fulltext_standardized,fulltext_ms,"
    "volpiano,node_id,position,folio,image_link"
)


def chant_csv(*rows: tuple[str, str]) -> str:
    """A CANTUS Database export with one chant per (folio, sequence)."""
    lines = [COLUMNS]
    for folio, sequence in rows:
        lines.append(
            f",{sequence},001234,Nativitas Domini,M,R,1,,,,Hodie,Hodie,Hodie,"
            f"1---g---,{sequence}0,1,{folio},"
        )
    return "\n".join(lines) + "\n"


class ImportChantsTestCase(TestCase):
    def setUp(self) -> None:
        self.manuscript = Manuscript.objects.create(
            id=7001,
            name="Live",
            siglum="LIVE-1",
            public=True,
            chants_loaded=True,
            is_mapped="MAPPED",
            csv_export_url="https://cantusdatabase.example/7001.csv",
        )
        self.folio = Folio.objects.create(
            number="001r", image_uri="https://img/001r", manuscript=self.manuscript
        )
        # A folio the new export no longer mentions.
        Folio.objects.create(
            number="099r", image_uri="https://img/099r", manuscript=self.manuscript
        )
        self.old_chants = {
            Chant.objects.create(
                manuscript=self.manuscript, folio=self.folio, sequence=s
            ).pk
            for s in (1, 2)
        }
        self.exemplar = create_fake_neume_exemplar(self.folio)
        self.submission = MEISubmission.objects.create(
            manuscript=self.manuscript,
            folio=self.folio,
            folio_number="001r",
            mei="<mei/>",
            submitter="asadra",
        )

    def run_import(self, csv_text: str = "", **patches) -> str:  # type: ignore[no-untyped-def]
        out = StringIO()
        download = patches or {"return_value": csv_text}
        with patch.object(Command, "_download_chant_csv", **download):
            with patch(GENRES, return_value={}):
                call_command("import_data", "chants", manuscript_id=7001, stdout=out)
        return out.getvalue()

    def chant_pks(self) -> set[int]:
        return set(
            Chant.objects.filter(manuscript=self.manuscript).values_list(
                "pk", flat=True
            )
        )

    def test_a_reimport_replaces_chants_and_keeps_folios(self) -> None:
        output = self.run_import(chant_csv(("001r", "1"), ("001r", "2"), ("002r", "3")))

        self.folio.refresh_from_db()
        self.assertEqual(self.folio.image_uri, "https://img/001r")
        self.assertTrue(NeumeExemplar.objects.filter(pk=self.exemplar.pk).exists())
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.folio_id, self.folio.pk)
        chants = self.chant_pks()
        self.assertEqual(len(chants), 3)
        self.assertFalse(chants & self.old_chants)
        self.assertEqual(
            Chant.objects.filter(folio=self.folio).count(), 2, "chants reuse the folio"
        )
        self.assertIn("099r (mapped)", output)
        self.assertIn("1 new folio(s) have no image yet", output)
        self.assertIn("002r", output)

    def test_a_failed_download_changes_nothing(self) -> None:
        Manuscript.objects.filter(pk=7001).update(chants_loaded=False)
        with self.assertRaises(URLError):
            self.run_import(side_effect=URLError("CANTUS Database is down"))
        self.assertEqual(self.chant_pks(), self.old_chants)
        self.assertEqual(Folio.objects.filter(manuscript=self.manuscript).count(), 2)
        self.assertFalse(Manuscript.objects.get(pk=7001).chants_loaded)

    def test_a_failure_while_saving_keeps_the_old_chants(self) -> None:
        real_save = Chant.save
        saved = []

        def save_then_fail(chant, *args, **kwargs):  # type: ignore[no-untyped-def]
            if saved:
                raise RuntimeError("database went away")
            saved.append(chant)
            return real_save(chant, *args, **kwargs)

        with patch.object(Chant, "save", save_then_fail):
            with self.assertRaises(RuntimeError):
                self.run_import(chant_csv(("001r", "1"), ("002r", "2")))
        self.assertEqual(self.chant_pks(), self.old_chants)
        self.assertFalse(
            Folio.objects.filter(manuscript=self.manuscript, number="002r").exists()
        )
