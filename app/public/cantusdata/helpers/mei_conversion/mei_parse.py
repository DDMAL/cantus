from lxml import etree

PITCH_VALUES = {
    "c": 1,
    "d": 2,
    "e": 3,
    "f": 4,
    "g": 5,
    "a": 6,
    "b": 7
}

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
    "dudd": "Porrectus subpunctis"
}

def contour_from_component_pair(prev: tuple, cur: tuple) -> str:
    (prev_note, prev_oct) = prev
    (cur_note, cur_oct) = cur
    if prev_oct > cur_oct:
        return "d"
    elif prev_oct < cur_oct:
        return "u"
    else:
        cur_pitch_value = PITCH_VALUES[cur_note.lower()]
        prev_pitch_value = PITCH_VALUES[prev_note.lower()]
        if prev_pitch_value > cur_pitch_value:
            return "d"
        elif prev_pitch_value < cur_pitch_value:
            return "u"
        else:
            return "s"

def get_streams(ncs: list) -> tuple:
    contour = ""
    pitches = ""
    intervals = ""
    prev = None
    for nc in ncs:
        #contour
        if prev != None:
            contour += contour_from_component_pair((prev.get("pname"), prev.get("oct")), (nc.get("pname"), nc.get("oct")))
        #pitch
        pitches += nc.get("pname").upper() + nc.get("oct") + ","
        #interval
            #translate pitches to numbers (whole or semitones) (and add 8*octave?)
            #subtract, +/-
        prev = nc
    
    return (contour, pitches, intervals)

def parse(file):
    tree = etree.parse(file)
    music = tree.getroot()[1]

    zones = {}
    surface = music[0][0]
    for zone in surface:
        zone_id = zone.get('{http://www.w3.org/XML/1998/namespace}id')
        ulx = int(zone.get("ulx", 0))
        uly = int(zone.get("uly", 0))
        lrx = int(zone.get("lrx", 0))
        lry = int(zone.get("lry", 0))
        rotation = zone.get("rotation", "0")
        region = f"{ulx},{uly},{lrx-ulx},{lry-uly}"
        zones["#"+zone_id] = {"region": region, "rotation": rotation}

    layer = music[1][0][0][1][0][0]

    (folio_contour, folio_pitches, folio_intervals) = get_streams(layer.iter("{http://www.music-encoding.org/ns/mei}nc"))

    neumes = []
    for syllable in layer.iter("{http://www.music-encoding.org/ns/mei}syllable"):
        syl = None
        for s in syllable.iter("{http://www.music-encoding.org/ns/mei}syl"):
            syl = s
        syl_dict = {"zone": zones.get(syl.get("facs"), ""), "text": syl.text.strip()}
        
        for neume in syllable.iter("{http://www.music-encoding.org/ns/mei}neume"):
            neume_zones = [zones.get(nc.get("facs"), "") for nc in neume]
            (contour, pitches, intervals) = get_streams(neume)
            neume_type = NEUME_GROUPS.get(contour, "Compound")
            neumes.append({"type": neume_type, "contour": contour, "pitches": pitches, "intervals": intervals, "zones": neume_zones, "syl": syl_dict})



#Basic idea for finding the containing neumes from a string of contours, pitches, intervals etc
def neumes_from_pitch_sequence(pitches: str, neumes: list) -> list:
    neume_lists = []
    for i, neume in enumerate(neumes):
        neume_pitches = neume["pitches"]
        if neume_pitches.startswith(pitches):
            return [neume]
        elif pitches.startswith(neume_pitches):
            last = find_last_neume_pitch(i+1, pitches[len(neume_pitches):], neumes)
            if last == -1:
                continue
            else:
                neume_list = []
                for j in range(i, last):
                    neume_list.append(neumes[j])
                neume_lists.append(neume_list)
    return neume_lists

def find_last_neume_pitch(next: int, remaining: str, neumes: list) -> int:
    if len(remaining) == 0:
        return next
    else:
        neume_pitches = neumes[next]["pitches"]
        if neume_pitches.startswith(remaining):
            return next+1
        elif remaining.startswith(neume_pitches):
            return find_last_neume_pitch(next+1, remaining[len(neume_pitches):], neumes)
        else:
            return -1

#this one needs to figure out the bridge entry between each neume
def neumes_from_contour_sequence(contour: str, neumes: list) -> list:
    neume_lists = []
    for i, neume in enumerate(neumes):
        neume_contour = neume["contour"]
        if neume_contour.startswith(contour):
            return [neume]
        elif contour.startswith(neume_contour):
            trailing_note_name = neume["pitches"][len(neume["pitches"])-3:]
            trailing_note = (trailing_note_name[0], trailing_note_name[1])

            last = find_last_neume_contour(i+1, contour[len(neume_contour):], trailing_note, neumes)
            if last == -1:
                continue
            else:
                neume_list = []
                for j in range(i, last):
                    neume_list.append(neumes[j])
                neume_lists.append(neume_list)
    return neume_lists

def find_last_neume_contour(next: int, remaining: str, trailing_note:dict, neumes: list) -> int:
    if len(remaining) == 0:
        return next
    elif next >= len(neumes):
        return -1
    else:
        cur = neumes[next]

        leading_note_name = cur["pitches"][0:3]
        leading_note = (leading_note_name[0], leading_note_name[1])
        bridge = contour_from_component_pair(trailing_note, leading_note)
        
        neume_contour = bridge + neumes[next]["contour"]
        if neume_contour.startswith(remaining):
            return next+1
        elif remaining.startswith(neume_contour):
            trailing_note_name = cur["pitches"][len(cur["pitches"])-3:]
            trailing_note = (trailing_note_name[0], trailing_note_name[1])
            return find_last_neume_contour(next+1, remaining[len(neume_contour):], trailing_note, neumes)
        else:
            return -1
