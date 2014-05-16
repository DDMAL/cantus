import csv


class CSVParser:

    file = None
    raw_data = list()
    column_names = list()
    parsed_data = list()

    def __init__(self, file_name):
        """
        Load the file and save the column names
        """
        self.file = open(u"{0}".format(file_name), 'r')
        reader = csv.reader(self.file)
        # The first row of the table contains labels, so we save them in labels.
        is_first = True
        for row in reader:
            if is_first:
                # Handles top row case
                self.column_names = row
                is_first = False
            else:
                # Handles other cases
                self.raw_data.append(row)
        # Construct the parsed data
        self.parse_data()

    def parse_data(self):
        """
        Produces a list of dictionaries with data labels
        """
        for row in self.raw_data:
            parsed_row = dict()
            # Add all of the row columns
            for i in xrange(len(row)):
                parsed_row[self.column_names[i]] = row[i]
            self.parsed_data.append(parsed_row)