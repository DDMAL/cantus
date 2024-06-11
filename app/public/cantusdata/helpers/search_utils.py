# Contains the words that are allowed
# in a neume_name query
VALID_NEUME_NAME_WORDS = {
    "punctum",
    "pes",
    "clivis",
    "scandicus",
    "torculus",
    "porrectus",
    "distropha",
    "tristopha",
    "pressus",
    "climacus",
    "resupinus",
    "flexus",
    "subpunctis",
    "compound",
}


def validate_query(q: list[str], q_type: str) -> bool:
    """
    Depending on the type of the query, returns True if the query is valid
    """
    match q_type:
        case "neume_names":
            return all(neume in VALID_NEUME_NAME_WORDS for neume in q)
        case "pitch_names" | "pitch_names_transposed":
            return all(pitch in "abcdefg" for pitch in q)
        case "contour":
            return all(contour in "udr" for contour in q)
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
