from io import StringIO
from typing import Iterable
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.core.management import CommandError, call_command
from django.test import TestCase

from cantusdata.models import Folio, Manuscript
from cantusdata.models.plugin import Plugin

IMPORTER = "cantusdata.management.commands.import_data.SourceImporter"


def source(source_id: int, **overrides: str) -> dict:
    data = {
        "id": source_id,
        "name": f"Source {source_id}",
        "siglum": f"S-{source_id}",
        "date": "12th century",
        "provenance": "Somewhere",
        "description": "A source.",
    }
    data.update(overrides)
    return data


class ImportManuscriptsTestCase(TestCase):
    def run_import(
        self,
        sources: dict[int, dict],
        failing: Iterable[int] = (),
        **options: bool,
    ) -> str:
        """Run `import_data manuscripts` against a stand-in CANTUS Database."""
        failing = set(failing)
        listed = sorted(set(sources) | failing)

        def get_source_data(source_id):  # type: ignore[no-untyped-def]
            if source_id in failing:
                raise HTTPError("url", 500, "Server Error", {}, None)  # type: ignore[arg-type]
            return sources[source_id]

        importer = MagicMock()
        importer.request_source_ids.return_value = [str(i) for i in listed]
        importer.get_source_data.side_effect = get_source_data
        out = StringIO()
        with patch(IMPORTER, return_value=importer):
            call_command("import_data", "manuscripts", stdout=out, **options)
        return out.getvalue()

    def test_local_work_survives_a_refresh(self) -> None:
        plugin = Plugin.objects.create(name="Neume Search")
        live = Manuscript.objects.create(
            id=100,
            name="Old name",
            public=True,
            chants_loaded=True,
            is_mapped="MAPPED",
            manifest_url="https://iiif.example/100/manifest.json",
            viewer_warning="Use Firefox",
        )
        live.plugins.add(plugin)

        output = self.run_import({100: source(100, name="New name"), 200: source(200)})

        live.refresh_from_db()
        self.assertEqual(live.name, "New name")
        self.assertTrue(live.public)
        self.assertTrue(live.chants_loaded)
        self.assertEqual(live.is_mapped, "MAPPED")
        self.assertEqual(live.manifest_url, "https://iiif.example/100/manifest.json")
        self.assertEqual(live.viewer_warning, "Use Firefox")
        self.assertEqual(list(live.plugins.all()), [plugin])
        created = Manuscript.objects.get(pk=200)
        self.assertEqual(created.is_mapped, "UNMAPPED")
        self.assertFalse(created.public)
        self.assertIn("Created 1, updated 1, unchanged 0", output)

    def test_unchanged_manuscripts_are_not_saved_again(self) -> None:
        sources = {100: source(100), 200: source(200)}
        self.run_import(sources)
        with patch.object(Manuscript, "save") as save:
            output = self.run_import(sources)
        save.assert_not_called()
        self.assertIn("updated 0, unchanged 2", output)

    def test_overlong_values_are_truncated_not_fatal(self) -> None:
        self.run_import({100: source(100, provenance="x" * 150)})
        self.assertEqual(len(Manuscript.objects.get(pk=100).provenance), 100)

    def test_too_many_failures_change_nothing(self) -> None:
        Manuscript.objects.create(id=100, name="Old name")
        with self.assertRaises(CommandError):
            self.run_import({100: source(100, name="New name")}, failing=[200, 300])
        self.assertEqual(Manuscript.objects.get(pk=100).name, "Old name")
        self.assertFalse(Manuscript.objects.filter(pk__in=[200, 300]).exists())

    def test_vanished_sources_are_only_listed_without_prune(self) -> None:
        Manuscript.objects.create(id=900, name="Gone")
        output = self.run_import({i: source(i) for i in range(1, 6)})
        self.assertTrue(Manuscript.objects.filter(pk=900).exists())
        self.assertIn("900", output)
        self.assertIn("--prune would delete", output)

    def test_prune_deletes_only_untouched_vanished_manuscripts(self) -> None:
        sources = {i: source(i) for i in range(1, 9)}
        Manuscript.objects.bulk_create([Manuscript(id=i) for i in sources])
        Manuscript.objects.create(id=900, name="Gone and untouched")
        Manuscript.objects.create(id=901, name="Gone but public", public=True)
        with_folio = Manuscript.objects.create(id=902, name="Gone with a folio")
        Folio.objects.create(number="001r", manuscript=with_folio)

        output = self.run_import(sources, prune=True)

        self.assertFalse(Manuscript.objects.filter(pk=900).exists())
        self.assertTrue(Manuscript.objects.filter(pk=901).exists())
        self.assertTrue(Manuscript.objects.filter(pk=902).exists())
        self.assertIn("kept (public)", output)
        self.assertIn("kept (has folios)", output)
        self.assertIn("pruned 1", output)

    def test_a_source_that_failed_to_download_has_not_vanished(self) -> None:
        sources = {i: source(i) for i in range(1, 9)}
        Manuscript.objects.create(id=9, name="Still listed")
        self.run_import(sources, failing=[9], prune=True)
        self.assertTrue(Manuscript.objects.filter(pk=9).exists())

    def test_prune_refuses_a_list_that_looks_partial(self) -> None:
        Manuscript.objects.bulk_create([Manuscript(id=i) for i in range(100, 110)])
        output = self.run_import({100: source(100)}, prune=True)
        self.assertEqual(Manuscript.objects.filter(pk__gte=100).count(), 10)
        self.assertIn("Not pruning", output)
