import csv


class CSVManager:
    def read(self, file_path):
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            return list(reader)