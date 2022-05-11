STEPREF = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}  # 2  # 9


def getIntervals(semitones, pnames):
    """Return a string encoding intervals, separated by underscores

    Get quality (major, minor, etc.) invariant interval name and direction
    for example, an ascending major second and an ascending minor second will
    both be encoded as 'u2'. the only tritone to occur is between b and f, in
    the context of this application we will assume that the b will always be
    sung as b  flat. So a tritone found in the music is never encoded as a
    tritone in our database; it will instead always be  represented as either a
    fifth or a fourth, depending on inversion. If the one wishes to search for
    tritones, they may use the semitones field.
    """
    intervals = []
    for (interval, pname) in zip(semitones, pnames):
        if interval == 0:
            intervals.append("r")
        else:
            if interval > 0:
                direction = "u"
            else:
                direction = "d"
            if interval == 6:
                if pname == "b":
                    size = 5
                else:
                    size = 4
            elif interval == -6:
                if pname == "b":
                    size = 4
                else:
                    size = 5
            else:
                size = abs(convertSemitoneToSpecifierGeneric(interval)[1])

            intervals.append("{0}{1}".format(direction, size))

    return "_".join(intervals)


def getContour(semitones):
    """Return semitones in Parson's Code

    Given a list of integers defining the size and direction of a series of
    musical intervals in semitones, this function encodes the contour of the
    melody with Parsons code for musical contour where u=up, d=down, r=repeat.
    """
    contour = []
    for p in semitones:
        if p == 0:
            contour.append("r")  # repeated
        elif p > 0:
            contour.append("u")  # up
        elif p < 0:
            contour.append("d")  # down

    return "".join(contour)


def getPitches(seq):
    """Return pitch names and MIDI values

    Given a list of MEI note elements, return the tuple (pnames, midipitch) where pnames is a string of the
    pitch names of the given notes (no octave information) and midipitch is a list of the midi values for those
    same pitches. Music21's convertStepToPs function is used to get midi pitch values.
    """
    pnames = []
    midipitch = []
    for note in seq:
        pnames.append(note.pitch_name)
        midipitch.append(int(convertStepToPs(note.pitch_name, note.octave)))

    return "".join(pnames), midipitch


def convertStepToPs(step, oct):
    """
    REMOVED FROM MUSIC21, so added here. -- AH

    Utility conversion; does not process internals.
    Takes in a note name string, octave number, and optional
    Accidental object.

    Returns a pitch space value as a floating point MIDI note number.

    >>> from music21 import *
    >>> pitch.convertStepToPs('c', 4, pitch.Accidental('sharp'))
    61.0
    >>> pitch.convertStepToPs('d', 2, pitch.Accidental(-2))
    36.0
    >>> pitch.convertStepToPs('b', 3, pitch.Accidental(3))
    62.0
    >>> pitch.convertStepToPs('c', 4, pitch.Accidental('half-flat'))
    59.5
    """
    step = step.strip().upper()
    ps = float(((oct + 1) * 12) + STEPREF[step])
    return ps


def convertSemitoneToSpecifierGeneric(count):
    """
    --- From music21 ---

    Given a number of semitones, return a default diatonic specifier.

    >>> interval.convertSemitoneToSpecifierGeneric(0)
    ('P', 1)
    >>> interval.convertSemitoneToSpecifierGeneric(-2)
    ('M', -2)
    >>> interval.convertSemitoneToSpecifierGeneric(1)
    ('m', 2)
    >>> interval.convertSemitoneToSpecifierGeneric(7)
    ('P', 5)
    >>> interval.convertSemitoneToSpecifierGeneric(11)
    ('M', 7)
    >>> interval.convertSemitoneToSpecifierGeneric(12)
    ('P', 8)
    >>> interval.convertSemitoneToSpecifierGeneric(13)
    ('m', 9)
    >>> interval.convertSemitoneToSpecifierGeneric(-15)
    ('m', -10)
    >>> interval.convertSemitoneToSpecifierGeneric(24)
    ('P', 15)
    """
    # strip off microtone
    return convertSemitoneToSpecifierGenericMicrotone(count)[:2]


def convertSemitoneToSpecifierGenericMicrotone(count):
    """
    --- From music21 ---

    Given a number of semitones, return a default diatonic specifier and cent offset.
    DEPRECATED if it can be moved..
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.5)
    ('M', 2, 50.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.25)
    ('M', 2, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.0)
    ('m', 2, 0.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.75)
    ('M', 2, -25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.9)
    ('M', 2, -10.0...)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(0.25)
    ('P', 1, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(12.25)
    ('P', 8, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(24.25)
    ('P', 15, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(23.75)
    ('P', 15, -25.0)
    """
    if count < 0:
        dirScale = -1
    else:
        dirScale = 1

    count, micro = divmod(count, 1)
    # convert micro to cents
    cents = micro * 100.0
    if cents > 50:
        cents -= 100
        count += 1

    count = int(count)
    size = abs(count) % 12
    octave = abs(count) // 12  # let floor to int

    if size == 0:
        spec = "P"
        generic = 1
    elif size == 1:
        spec = "m"
        generic = 2
    elif size == 2:
        spec = "M"
        generic = 2
    elif size == 3:
        spec = "m"
        generic = 3
    elif size == 4:
        spec = "M"
        generic = 3
    elif size == 5:
        spec = "P"
        generic = 4
    elif size == 6:
        spec = "d"
        generic = 5
    elif size == 7:
        spec = "P"
        generic = 5
    elif size == 8:
        spec = "m"
        generic = 6
    elif size == 9:
        spec = "M"
        generic = 6
    elif size == 10:
        spec = "m"
        generic = 7
    elif size == 11:
        spec = "M"
        generic = 7

    return spec, (generic + (octave * 7)) * dirScale, cents
