import re


def get_transpositions(sequence):
    """ Given a series of pitch names (no flats or sharps - just abcdefg),
    return a list of the 7 possible transpositions of the melody. This is used
    when generating an elastic search query to look for all transpositions of a
    user specified pitch sequence.

    The URL for the query will include 'q=pnames:' followed by the returned
    transpositions seperated by commas.

    e.g. getTranspositions('cece') returns ['cece', 'dfdf', 'egeg', 'fafa',
    'gbgb', 'acac', 'bdbd']
    """
    sequence = str(sequence)
    asciinum = map(ord, sequence)

    def transposeUp(x):
        if x < 103:
            return x+1
        else:
            return x-6
    transpositions = [sequence]

    for i in range(1, 7):
        asciinum = map(transposeUp, asciinum)
        transposed = ''.join(chr(i) for i in asciinum)  # convert to string
        transpositions = transpositions + [transposed]
    return transpositions


def get_neumes_length(neumes):
    lengths = {
        'punctum': 1,
        'virga': 1,
        'bivirga': 2,
        'podatus': 2,
        'pes': 2,
        'clivis': 2,
        'epiphonus': 2,
        'cephalicus': 2,
        'scandicus': 3,
        'salicus': 3,
        'ancus': 3,
        'torculus': 3,
        'porrectus': 3,
        # Treat flexus as a different one so we can have porrectus flexus, etc
        'resupinus': 1,
        'flexus': 1,
        'cavum': 1,
    }

    neumes = neumes.lower().split(' ')
    length = 0
    for neume in neumes:
        if lengths.has_key(neume):
            length += lengths[neume]
        else:
            # In case their is a type of neume that we don't recognize!
            length += 1

    return length


def valid_pitch_sequence(sequence):
    # Should already be lowercase
    pattern = re.compile("[^a-g]")
    if pattern.search(sequence) is not None:
        return False
    else:
        return True


def valid_contour_sequence(sequence):
    # Already lowercase
    pattern = re.compile("[^rud]")
    if pattern.search(sequence) is not None:
        return False
    else:
        return True
