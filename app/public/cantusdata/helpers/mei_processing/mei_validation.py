"""
Validation of MEI documents at the point they enter the system.

An MEI file is only useful to Cantus Ultimus if MEIParser can read it and it
actually contains notation. Checking that when a document is submitted -- rather
than when an admin publishes it -- means the failure is reported to the person
who can still fix it, instead of surfacing inside a review action after the
document has already been approved.
"""

from os import path
from shutil import rmtree
from tempfile import mkdtemp

from lxml.etree import XMLSyntaxError  # pylint: disable=no-name-in-module

from .mei_parser import MEIParser


class MEIValidationError(ValueError):
    """Raised when an MEI document cannot be parsed or contains no notation."""


def validate_mei_document(mei: str) -> int:
    """
    Parse an MEI document and confirm it contains notation.

    :param mei: The contents of an MEI file.
    :return: The number of neumes found in the document.
    :raises MEIValidationError: If the document is not well-formed XML, cannot be
        parsed by MEIParser, or contains no neumes.
    """
    # MEIParser takes a path, so the document has to reach the filesystem to be
    # checked. The temporary directory is removed before returning either way.
    tmp_dir = mkdtemp(prefix="mei-validate-")
    try:
        tmp_path = path.join(tmp_dir, "submission.mei")
        with open(tmp_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(mei)
        try:
            parser = MEIParser(tmp_path)
        except XMLSyntaxError as exc:
            raise MEIValidationError(f"Not well-formed XML: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise MEIValidationError(f"Could not be parsed as MEI: {exc}") from exc
        neume_count = sum(len(syllable["neumes"]) for syllable in parser.syllables)
        if neume_count == 0:
            raise MEIValidationError(
                "Parsed successfully but contains no neumes, so it would add "
                "nothing to the notation index."
            )
        return neume_count
    finally:
        rmtree(tmp_dir, ignore_errors=True)
