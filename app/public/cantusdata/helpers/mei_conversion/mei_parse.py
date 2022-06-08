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

def get_streams(ncs: list) -> tuple:
    contour = ""
    pitches = ""
    intervals = ""
    prev = None
    for nc in ncs:
        #contour
        if prev != None:
            if prev.get("oct") > nc.get("oct"):
                contour += "d"
            elif prev.get("oct") < nc.get("oct"):
                contour += "u"
            else:
                pitch_value = PITCH_VALUES[nc.get("pname")]
                prev_pitch_value = PITCH_VALUES[prev.get("pname")]
                if pitch_value < prev_pitch_value:
                    contour += "u"
                elif pitch_value > prev_pitch_value:
                    contour += "d"
                else:
                    contour += "s"
        #pitch
        pitches += nc.get("pname").upper() + nc.get("oct") + ","
        #interval

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



#This basic idea can be used to find the containing neumes from a string of contours, pitches, intervals as well
def zones_from_chant_text(chant_text: str, syllables: list) -> list:
    chant_text = chant_text.replace(" ", "").lower()
    for i, syllable in enumerate(syllables):
        syl_text = syllable["syl"]["text"]
        if chant_text[0:len(syl_text)] == syl_text.lower():
            last = find_end_syl(i+1, chant_text[len(syl_text):])
            if last == -1:
                continue
            else:
                text_zones = []
                for j in range(i, last):
                    zone = syllables[j]["syl"]["zone"]
                    text_zones.append(zone)
                return text_zones

def find_end_syl(next: int, remaining: str, syllables: list) -> int:
    if len(remaining) == 0:
        return next
    else:
        syl_text = syllables[next]["syl"]["text"]
        if remaining[0:len(syl_text)] == syl_text.lower():
            return find_end_syl(next+1, remaining[len(syl_text):])
        else:
            return -1

#print(zones_from_chant_text("Qui regis Israhel"))# intende qui deducis velut ovem Joseph qui sedes super cherubim"))