

class BoundingBox():
    ulx = None
    uly = None
    lrx = None
    lry = None
    name = None

    def __unicode__(self):
        return u"neume[name: {0}, ulx: {1}, uly: {2}, lrx: {3}, lry: {4}]".format(self.name, self.ulx, self.uly, self.lrx, self.lry)

    def get_width(self):
        return int(self.lrx) - int(self.ulx)

    def get_height(self):
        return int(self.lry) - int(self.uly)
