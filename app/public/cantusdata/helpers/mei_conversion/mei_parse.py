from lxml import etree
import xml.etree.ElementTree as ET

PITCH_CLASS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

NEUME_GROUPS = {
    "": "Punctum",
    "u": "Pes",
    "d": "Clivis",
    "uu": "Scandicus",
    "ud": "Torculus",
    "du": "Porrectus",
    "s": "Distropha",
    "ss": "Tristopha",
    "sd": "Pressus",
    "dd": "Climacus",
    "ddu": "Climacus resupinus",
    "udu": "Torculus resupinus",
    "dud": "Porrectus flexus",
    "udd": "Pes subpunctis",
    "uud": "Scandicus flexus",
    "uudd": "Scandicus subpunctis",
    "dudd": "Porrectus subpunctis",
}

MEINS = "{http://www.music-encoding.org/ns/mei}"
XMLNS = "{http://www.w3.org/XML/1998/namespace}"


def parse_pitch(p):
    """Converts a pitch string into (pitch, octave)."""
    # The octave should always be the last character
    return p[:-1], int(p[-1])


def pitch_to_midi(p):
    """Converts a pitch string into a midi note number."""
    note, oct = parse_pitch(p)
    return PITCH_CLASS[note] + (12 * (oct + 1))


def interval(p1, p2):
    """Provides the interval in semitones."""
    return pitch_to_midi(p2) - pitch_to_midi(p1)


def contour_from_pitches(p1, p2):
    """Computes the contour between two pitches."""
    contour_from_interval(interval(p1, p2))


def contour_from_interval(semitones):
    """Computes the contour of an interval."""
    if semitones < 0:
        return "d"
    elif semitones > 0:
        return "u"
    else:
        return "s"


def parse_zones(mei):
    """Get the zones (bounding boxes) from an MEI root element."""
    zones = {}
    for zone in mei.iter(f"{MEINS}zone"):
        zone_id = zone.get(f"{XMLNS}id")
        coordinate_names = ["ulx", "uly", "lrx", "lry"]
        coordinates = [int(zone.get(c, 0)) for c in coordinate_names]
        rotate = float(zone.get("rotate", 0.0))
        zones[f"#{zone_id}"] = {
            "coordinates": tuple(coordinates),
            "rotate": rotate,
        }
    return zones


def parse_neumes(mei, zones):
    """Get all neume groupings and global pitch|interval|contour sequences."""
    neumes = []
    global_pitches = []
    for syllable in mei.iter(f"{MEINS}syllable"):
        syl = syllable.find(f"{MEINS}syl")
        syltext = syl.text.strip()
        syl_facs = syl.get("facs")
        syl_coordinates = zones.get(syl_facs, (-1, -1, -1, -1))
        for neume in syllable.findall(f"{MEINS}neume"):
            pitches = []
            nc_coordinates = []
            for nc in neume:
                pname = nc.get("pname")
                oct = nc.get("oct")
                facs = nc.get("facs")
                coordinates = zones.get(facs, (-1, -1, -1, -1))
                pitches.append(f"{pname}{oct}")
                nc_coordinates.append(coordinates)
            global_pitches.extend(pitches)
            pitches_pairs = list(zip(global_pitches[:-1], global_pitches[1:]))
            intervals = [interval(p1, p2) for p1, p2 in pitches_pairs]
            contours = [contour_from_interval(i) for i in intervals]
            neume_type = NEUME_GROUPS.get("".join(contours), "Compound")
            neume_dict = {
                "neume_type": neume_type,
                "nc_coordinates": nc_coordinates,
                "syl_coordinates": syl_coordinates,
                "pitches": pitches,
                "intervals": intervals,
                "contours": contours,
                "lyric": syltext,
            }
            neumes.append(neume_dict)
    global_pitches_pairs = list(zip(global_pitches[:-1], global_pitches[1:]))
    global_intervals = [interval(p1, p2) for p1, p2 in global_pitches_pairs]
    global_contours = [contour_from_interval(i) for i in global_intervals]
    global_sequences = {
        "pitches": global_pitches,
        "intervals": global_intervals,
        "contours": global_contours,
    }
    return neumes, global_sequences


def parse(file):
    tree = ET.parse(file)
    mei = tree.getroot()
    zones = parse_zones(mei)
    neumes, global_sequences = parse_neumes(mei, zones)
    return neumes, global_sequences