from os import path

from django.conf import settings
from django.test import TestCase

from cantusdata.helpers.mei_processing.mei_validation import (
    MEIValidationError,
    validate_mei_document,
)

MEI_FIXTURE = path.join(
    settings.TEST_MEI_FILES_PATH, "123723", "cdn-hsmu-m2149l4_001r.mei"
)


class ValidateMEIDocumentTestCase(TestCase):
    """
    Validation of MEI arriving from outside, over the deposit API.

    These documents are untrusted input parsed server-side, so the parser's
    handling of entities is part of the contract, not an implementation detail.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        with open(MEI_FIXTURE, encoding="utf-8") as mei_file:
            cls.valid_mei = mei_file.read()

    def test_a_real_mei_document_reports_its_neume_count(self) -> None:
        self.assertGreater(validate_mei_document(self.valid_mei), 0)

    def test_malformed_xml_is_reported_as_a_validation_error(self) -> None:
        with self.assertRaises(MEIValidationError) as raised:
            validate_mei_document("<mei><unclosed>")
        self.assertIn("Not well-formed XML", str(raised.exception))

    def test_well_formed_xml_without_neumes_is_refused(self) -> None:
        with self.assertRaises(MEIValidationError):
            validate_mei_document('<?xml version="1.0"?><mei/>')

    def test_an_external_entity_is_not_resolved(self) -> None:
        """
        An MEI document must not be able to read a file off the server by
        declaring an external entity for it. lxml has refused this by default
        since version 5, but the default was the opposite before that, so the
        parser now states it rather than inheriting it -- and this test fails if
        that is ever loosened.

        The document is refused outright (the entity is undefined), which reaches
        the submitter as a validation error rather than as a leak.
        """
        with open(MEI_FIXTURE, encoding="utf-8") as mei_file:
            secret_path = mei_file.name
        xxe = (
            '<?xml version="1.0"?>'
            f'<!DOCTYPE mei [ <!ENTITY leak SYSTEM "file://{secret_path}"> ]>'
            "<mei><note>&leak;</note></mei>"
        )
        with self.assertRaises(MEIValidationError) as raised:
            validate_mei_document(xxe)
        # Specifically the parse failing on an undefined entity. A permissive
        # parser would expand the entity, parse happily, and then fail this
        # document for having no neumes -- also an MEIValidationError, which is
        # why the message is asserted rather than just the exception type.
        self.assertIn("Not well-formed XML", str(raised.exception))
        self.assertIn("leak", str(raised.exception))

    def test_an_internal_entity_still_expands(self) -> None:
        """
        Only *external* entities are refused. A document declaring its own
        entities in its internal subset is ordinary XML and must still parse --
        it fails validation for having no neumes, not for being malformed.
        """
        internal = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE mei [ <!ENTITY title "Antiphonarium"> ]>'
            "<mei><title>&title;</title></mei>"
        )
        with self.assertRaises(MEIValidationError) as raised:
            validate_mei_document(internal)
        self.assertNotIn("Not well-formed XML", str(raised.exception))
