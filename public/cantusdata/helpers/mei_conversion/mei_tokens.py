"""Represents a single constituent of the *** indexed in an n-gram"""


class MissingSystemBreak (object):
    """Dummy object used in cases where a system break is missing"""
    pass


class NeumeToken (object):
    def __init__(self, uuid, name, system, location, elem=None):
        self.uuid = uuid
        self.name = name
        self.system = system
        self.location = location
        self.elem = elem

    def get_notes(self):
        if not self.elem:
            return

        for note in self.elem.getDescendantsByName('note'):
            yield NoteToken.from_elem(note, neume=self)

    @staticmethod
    def get_all_from_doc(doc):
        zones = {zone.getId(): zone for zone in doc.getElementsByName('zone')}

        for layer in doc.getElementsByName('layer'):
            # Get a unique key when the initial <sb> is missing
            system_id = MissingSystemBreak()

            for child in layer.getChildren():
                name = child.getName()

                if name == 'sb':
                    system_id = child.getId()

                elif name == 'neume':
                    zone = zones[child.getAttribute('facs').value]
                    yield NeumeToken.from_elem(child, system=system_id, zone=zone)

    @staticmethod
    def from_elem(elem, system, zone):
        uuid = elem.getId()
        name = elem.getAttribute('name').value

        location = {}

        for attr in ('ulx', 'uly', 'lrx', 'lry'):
            location[attr] = int(zone.getAttribute(attr).value)

        return NeumeToken(uuid, name=name, system=system, location=location, elem=elem)


class NoteToken (object):
    def __init__(self, uuid, pitch_name, octave, neume):
        self.uuid = uuid
        self.pitch_name = pitch_name
        self.octave = octave
        self.neume = neume

    @staticmethod
    def from_elem(elem, neume):
        uuid = elem.getId()

        pitch_name = elem.getAttribute('pname').value

        if len(pitch_name) != 1:
            raise ValueError('expected note pname to be a single character but got {!r}'.format(pitch_name))

        octave = int(elem.getAttribute('oct').value)

        return NoteToken(uuid, pitch_name=pitch_name, octave=octave, neume=neume)
