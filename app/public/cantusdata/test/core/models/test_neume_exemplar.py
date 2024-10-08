from django.test import TestCase
from cantusdata.models import NeumeExemplar, Manuscript, Folio

from cantusdata.test.core.fake_generators import create_fake_neume_exemplar


class NeumeExemplarModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        manuscript = Manuscript.objects.create(
            id=1,
            name="Manuscript 1",
        )
        f001r = Folio.objects.create(
            manuscript=manuscript,
            number="001r",
            image_uri="https://example.com/f001r.jpg",
        )
        f001v = Folio.objects.create(
            manuscript=manuscript,
            number="001v",
            image_uri="https://example.com/f001v.jpg",
        )
        for neume_name, folio in [
            ("scandicus", f001v),
            ("porrectus-flexus", f001r),
            ("compound", f001v),
            ("punctum", f001r),
        ]:
            create_fake_neume_exemplar(folio, name=neume_name)

    def test_ordering(self) -> None:
        """
        Test that default ordering is correct (ie. that the custom
        save method is working correctly).
        """
        exemplars = NeumeExemplar.objects.all()
        self.assertEqual(
            [exemplar.name for exemplar in exemplars],
            ["punctum", "scandicus", "porrectus-flexus", "compound"],
        )
