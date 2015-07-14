from PIL import Image, ImageDraw


class RunLengthImage():
    ulx = None
    uly = None
    width = None
    height = None
    run_length_data = None

    def __init__(self, ulx, uly, width, height, run_length_data):
        self.ulx = ulx
        self.uly = uly
        self.width = width
        self.height = height
        # Turn run-length data into list of ints
        self.run_length_data = map(lambda x: int(x), run_length_data.split())

    def get_location_of_runlength(self, pixel_number):
        """
        Find the x,y location of the nth pixel of a run-length encoding.

        :param pixel_number: nth pixel, starting at 0 and ending at
         width * height - 1
        :return: (x,y) tuple
        """
        y = pixel_number / self.width
        x = pixel_number % self.width
        return x, y

    def get_image(self):
        image = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(image)
        current_pixel = 0
        is_black = False
        # Iterate through the run length data
        for length in self.run_length_data:
            for n in range(length):
                # 0 = white, 1 = black
                colour = 'white'
                if is_black:
                    colour = 'black'
                # Paint the pixel to the image
                draw.point(self.get_location_of_runlength(current_pixel), fill=colour)
                # Increase the current pixel
                current_pixel += 1
            # Switch from black to white or white to black
            is_black = not is_black
        # We're done drawing
        del draw
        return image

    def __unicode__(self):
        return u"run_length_image[{0}, {1}, {2}, {3}]".format(self.ulx,
                                                              self.uly,
                                                              self.width,
                                                              self.height)
