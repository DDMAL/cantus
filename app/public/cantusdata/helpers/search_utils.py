"""
A collection of functions used by search views to validate and process
queries.
"""

from cantusdata.helpers.neume_helpers import NEUME_NAMES


def validate_intervals_query_word(word: str) -> bool:
    """
    Returns True if the "word" is valid in an intervals query.

    Valid words are one of the letters "u"[p], "d"[own], "r"[epeat].
    A "u" or "d" must be followed by a positive integer > 1.
    """
    if word == "r":
        return True
    if word[0] in {"u", "d"}:
        interval_mag = word[1:]
        if interval_mag.isdigit() and interval_mag != "1":
            return True
    return False


def validate_query(q: list[str], q_type: str) -> bool:
    """
    Depending on the type of the query, returns True if the query is valid
    """
    match q_type:
        case "neume_names":
            return all(neume in NEUME_NAMES for neume in q)
        case "pitch_names" | "pitch_names_transposed":
            return all(pitch in "abcdefg" for pitch in q)
        case "contour":
            return all(contour in "udr" for contour in q)
        case "intervals":
            return all(validate_intervals_query_word(word) for word in q)
        case _:
            return False


def transpose_up_unicode(x: int) -> int:
    """
    Transpose up the unicode decimal for a pitch
    name up 1 step. The unicode decimal for "g" is 103,
    so to transpose up from "g" to "a", we need to subtract 6.
    We can transpose up all other pitch names by adding 1.
    """
    # x is the unicode decimal for "a-f"
    if x < 103:
        return x + 1
    # x is the unicode decimal for "g"
    return x - 6


def get_transpositions(sequence: list[str]) -> list[list[str]]:
    """
    Given a series of pitch names (no flats or sharps - just abcdefg),
    return a list of the 7 possible transpositions of the melody.

    e.g. get_transpositions('cece') returns ['cece', 'dfdf', 'egeg', 'fafa',
    'gbgb', 'acac', 'bdbd']
    """
    # Get the unicode decimal for each character in the sequence
    asciinum = list(map(ord, sequence))

    transpositions = [sequence]

    for _ in range(1, 7):
        asciinum = list(map(transpose_up_unicode, asciinum))
        transposed_chars = list(map(chr, asciinum))
        transpositions.append(transposed_chars)
    return transpositions


def translate_interval_query_direction(query_terms: list[str]) -> list[str]:
    """
    Translate the terms of an interval query (alphanumeric strings; e.g. "u3", "d2", "r")
    as entered by a user into the format that is used in the Solr query (integer strings;
    e.g. "3", "-2", "1").

    Terms are translated as follows:
    - "r" translates to "1"
    -  a "u" indicates an ascending interval, and it translated to a positive
        integer
    -  a "d" indicates a descending interval, and it translated to a negative
        integer

    :param query_terms: a list of strings representing the terms of the interval query;
        it is assumed that these have already been validated by validate_intervals_query_word

    :return: a list of strings representing the terms of the interval query in the format
        used in the Solr query
    """
    solr_query: list[str] = []
    for term in query_terms:
        if term == "r":
            solr_query.append("1")
        else:
            direction = "-" if term[0] == "d" else ""
            magnitude = term[1:]
            solr_query.append(f"{direction}{magnitude}")
    return solr_query
