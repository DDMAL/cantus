from .abstract_mei_converter import AbstractMEIConverter


class MEIConverter (AbstractMEIConverter):
    def getNeumes(self, seq, counter):
        return AbstractMEIConverter.getNeumes(self, seq, counter)

    def getLocation(self, seq, meifile, zones):
        return AbstractMEIConverter.getLocation(self, seq, meifile, zones)

    def processMeiFile(self, ffile):
        return AbstractMEIConverter.processMeiFile(self, ffile)
