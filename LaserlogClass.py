import pandas as pd
import SampleinlogClass


class Laserlog:
    def __init__(self, experiment, clean_laserlog_dataframe: pd.DataFrame, name: str):
        self.experiment = experiment
        self.clean_laserlog_dataframe = clean_laserlog_dataframe
        self.sampleinlog_objects_dictionary = {}
        self.name = name

    def divide_clean_logfile_dataframe_into_samples(self):
        df = self.clean_laserlog_dataframe
        sample_chunks_dictionary: dict = {}
        sample_chunks_dictionary[f'Sample_1'] = df
        return sample_chunks_dictionary

    def build_sampleinlog_objects(self):
        sample_chunks_dictionary = self.divide_clean_logfile_dataframe_into_samples()
        if sample_chunks_dictionary is False:
            return False
        for sample_number, logfile in sample_chunks_dictionary.items():
            sampleinlog = SampleinlogClass.Sampleinlog(sample=sample_number,
                                                       logfile_slice=logfile,
                                                       log=self)

            self.sampleinlog_objects_dictionary[sample_number] = sampleinlog
        return True

    def get_log_information_of_rawdata_sample(self, sample_number: str):
        return self.sampleinlog_objects_dictionary[sample_number].get_true_line_information_dictionary(), self.sampleinlog_objects_dictionary[sample_number].get_outer_dimensions_dictionary(), self.sampleinlog_objects_dictionary[sample_number].get_scan_speed()

    def send_error_message(self, title, message):
        self.experiment.send_error_message(title=title, message=message)

    def export(self, dictionary):
        return self.experiment.export_pattern_duration_data(dictionary=dictionary, name=self.name)

    def get_sampleinlog_objects_dictionary(self):
        return self.sampleinlog_objects_dictionary


