from music21.pitch import STEPREF
from music21.interval import convertSemitoneToSpecifierGeneric


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
            intervals.append('r')
        else:
            if interval > 0:
                direction = 'u'
            else:
                direction = 'd'
            if interval == 6:
                if pname == 'b':
                    size = 5
                else:
                    size = 4
            elif interval == -6:
                if pname == 'b':
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
            contour.append('r')  # repeated
        elif p > 0:
            contour.append('u')  # up
        elif p < 0:
            contour.append('d')  # down

    return ''.join(contour)


def getPitches(seq):
    """Return pitch names and MIDI values

    Given a list of MEI note elements, return the tuple (pnames, midipitch) where pnames is a string of the
    pitch names of the given notes (no octave information) and midipitch is a list of the midi values for those
    same pitches. Music21's convertStepToPs function is used to get midi pitch values.
    """
    pnames = []
    midipitch = []
    for note in seq:
        pnames.append(note.getAttribute("pname").value[0])  # a string of pitch names e.g. 'gbd'

        step = str(note.getAttribute("pname").value[0])
        octave = int(note.getAttribute("oct").value)
        midipitch.append(int(convertStepToPs(step, octave)))

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
