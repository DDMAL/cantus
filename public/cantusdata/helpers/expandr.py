

def ordinal(value):
    """
    Converts zero or a *postive* integer (or their string
    representations) to an ordinal value.

    >>> for i in range(1,13):
    ...     ordinal(i)
    ...
    u'1st'
    u'2nd'
    u'3rd'
    u'4th'
    u'5th'
    u'6th'
    u'7th'
    u'8th'
    u'9th'
    u'10th'
    u'11th'
    u'12th'

    >>> for i in (100, '111', '112',1011):
    ...     ordinal(i)
    ...
    u'100th'
    u'111th'
    u'112th'
    u'1011th'

    """
    try:
        value = int(value)
    except ValueError:
        return value

    if value % 100//10 != 1:
        if value % 10 == 1:
            ordval = u"%d%s" % (value, "st")
        elif value % 10 == 2:
            ordval = u"%d%s" % (value, "nd")
        elif value % 10 == 3:
            ordval = u"%d%s" % (value, "rd")
        else:
            ordval = u"%d%s" % (value, "th")
    else:
        ordval = u"%d%s" % (value, "th")

    return ordval

def feast_code_lookup(feast_code, feast_file):
    # f = [r for r in feastfile if r['FeastCode'] == feastcode]
    for record in feast_file:
        if not record["FeastCode"]:
            continue
        if len(record["FeastCode"]) == 7:
            record["FeastCode"] = "0{0}".format(record["FeastCode"])
        if str(record["FeastCode"]) == str(feast_code):
            return record["EnglishName"]
    return None

def expand_position(position, genre, office):
    output = None
    if position.isdigit():
        if genre == "Hymn" or genre == "Responsory Verse":
            temp_string = "Hymn Verse" if genre == "Hymn" else "Verse"
            output = "{0} {1}".format(temp_string, position.lstrip("0"))
        elif genre == "Versicle":
            output = "{0} {1}".format(ordinal(int(position)), genre)
        elif office in ("Lauds", "First Vespers", "Second Vespers", "Terce") and genre != "Hymn":
            output = "{0} for the {1} Psalm".format("Antiphon", ordinal(int(position)))
        elif office == "Matins" and genre in ("Responsory", "Antiphon"):
            temp_string = "Lessons" if genre == "Responsory" else "Psalms"
            output = "{0} for all {1} of Nocturn {2}".format(
                position.lstrip("0"), temp_string, position)
        elif office == "Matins" and genre == "Antiphon Verse":
            output = "{0} {1}".format(genre, position.lstrip("0"))
    else:
        if position == "p":
            output = "Antiphon for all Psalms/Canticles"
        elif "." in position:
            if len(position) == 3:
                noc, les = position.split(".")
                temp_string = "Psalm" if genre == "Antiphon" else "Lesson"
                output = "{0} for Nocturn {1}, {2} {3}".format(genre, noc, temp_string, les)
            else:
                noc, nul = position.split(".")
                output = "Antiphon for all Psalms of Nocturn {0}".format(noc)
        elif position == "M":
            output = "Antiphon for the Magnificat"
        elif position == "B":
            output = "Antiphon for the Benedictus"
        elif position == "N":
            output = "Antiphon for the Nunc Dimittis"
        elif position == "R":
            output = "Antiphon sung as a memorial"
        elif len(position) == 2:
            if position[1] == "B":
                output = "{0} Antiphon for the Benedictus".format(ordinal(int(position[0])))
            elif position[1] == "M":
                output = "{0} Antiphon for the Magnificat".format(ordinal(int(position[0])))
    return output

def expand_mode(input):
    input_list = input.strip().split()
    mode_output = []
    if "1" in input_list:
        mode_output.append("Mode 1")
    if "2" in input_list:
        mode_output.append("Mode 2")
    if "3" in input_list:
        mode_output.append("Mode 3")
    if "4" in input_list:
        mode_output.append("Mode 4")
    if "5" in input_list:
        mode_output.append("Mode 5")
    if "6" in input_list:
        mode_output.append("Mode 6")
    if "7" in input_list:
        mode_output.append("Mode 7")
    if "8" in input_list:
        mode_output.append("Mode 8")
    if "*" in input_list:
        mode_output.append("No music")
    if "r" in input_list:
        mode_output.append("Responsory (simple)")
    if "?" in input_list:
        mode_output.append("Uncertain")
    if "S" in input_list:
        mode_output.append("Responsory (special)")
    if "T" in input_list:
        mode_output.append("Chant in Transposition")
    outstring = " ".join(mode_output)
    return outstring

def expand_genre(input):
    return {
        "A":"Antiphon",
        "AV": "Antiphon Verse",
        "R": "Responsory",
        "V": "Responsory Verse",
        "W": "Versicle",
        "H": "Hymn",
        "I": "Invitatory antiphon",
        "P": "Invitatory Psalm",
        "M": "Miscellaneous",
        "G": "Mass chants"
    }.get(input, "Error")

def expand_office(input):
    return {
        "V": "First Vespers",
        "C": "Compline",
        "M": "Matins",
        "L": "Lauds",
        "P": "Prime",
        "T": "Terce",
        "S": "Sext",
        "N": "None",
        "V2": "Second Vespers",
        "D": "Day Hours",
        "R": "Memorial",
        "E": "Antiphons for the Magnificat or Benedictus",
        "H": "Antiphons based on texts from the Historia",
        "CA": "Chapter",
        "X": "Supplementary"
    }.get(input, "Error")