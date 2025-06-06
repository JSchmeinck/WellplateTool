from typing import Optional
import SampleinlogClass


class RawdataSample:
    def __init__(self, experiment, rawdata_dictionary, name, sample_number, column_names, mass_list):
        self.experiment = experiment
        self.name = name
        self.sample_number = sample_number
        self.rawdata_dictionary: dict = rawdata_dictionary
        self.sample_in_log: SampleinlogClass.Sampleinlog
        self.amount_of_lines = 0
        self.sample_in_log: Optional[SampleinlogClass.Sampleinlog] = None
        self.list_of_column_names: list = column_names
        self.mass_list = mass_list


    def get_data(self, analyte):
        return self.rawdata_dictionary[analyte]


    def set_sample_in_log(self, sample_in_log):
        self.sample_in_log = sample_in_log

    def get_amount_of_lines(self):
        return self.amount_of_lines

    def send_error_message(self, title, message):
        self.experiment.send_error_message(title=title, message=message)




