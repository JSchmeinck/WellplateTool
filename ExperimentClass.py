import os
from typing import Optional
import pandas as pd
import numpy as np
import LaserlogClass
import RawdataSampleClass
import OutlierDetection


class Experiment:
    def __init__(self, gui, raw_laser_logfile_dataframe: pd.DataFrame, sample_rawdata_dictionary: dict, data_type: str,
                 logfile_filepath: str, synchronized: bool):
        self.gui = gui
        self.raw_laser_logfile_dataframe: pd.DataFrame = raw_laser_logfile_dataframe
        self.sample_rawdata_dictionary: dict = sample_rawdata_dictionary
        self.data_type = data_type
        self.laserlog_object: Optional[LaserlogClass.Laserlog] = None
        self.RawdataSample_objects_dictionary: dict = {}
        self.logfile_filepath: str = logfile_filepath
        self.synchronized = synchronized
        self.rectangles_dictionary = {}

        self.putative_value_arsenic = None
        self.decider_value_arsenic = None
        self.putative_value_copper = None
        self.decider_value_copper = None

    def build_laser_log_object(self):

        filtered_df = self.raw_laser_logfile_dataframe
        filtered_df = filtered_df.reset_index(drop=True)
        name = os.path.basename(self.logfile_filepath).removesuffix('.csv')
        self.laserlog_object = LaserlogClass.Laserlog(experiment=self,
                                                      clean_laserlog_dataframe=filtered_df,
                                                      name=name)


    def build_rawdatasample_objects(self):
        sample_counter = 1
        for sample_name, sample_rawdata_dataframe in self.sample_rawdata_dictionary.items():
            rawdata_extracted_masses_dictionary = {}
            synchronized_data, list_of_unique_masses_in_file, time_data_sample = self.gui.synchronizer.get_data(
                sample_name=sample_name)

            list_of_col_names = []
            self.gui.widgets.choose_data_combobox['values'] = list_of_unique_masses_in_file
            for k, i in enumerate(list_of_unique_masses_in_file):
                extracted_sample_column_dictionary = {}
                for col in synchronized_data.columns:
                    if col != 'Unnamed: 2':
                        if k == 0:
                            list_of_col_names.append(col)
                        filtered_values = synchronized_data[synchronized_data['Unnamed: 2'] == i][col].values
                        extracted_values = np.array(filtered_values)
                        extracted_array = extracted_values.astype(float)
                        extracted_array = extracted_values[~np.isnan(extracted_array)]
                        extracted_array = extracted_array.astype(float)


                        extracted_sample_column_dictionary[col] = extracted_array
                rawdata_extracted_masses_dictionary[i] = extracted_sample_column_dictionary
            rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                             name=sample_name,
                                                             rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                             sample_number=f'Sample_{sample_counter}',
                                                             column_names=list_of_col_names,
                                                             mass_list=list_of_unique_masses_in_file)
            self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

    def pass_sample_logfile_information(self, sample_number: str):
        return self.laserlog_object.get_log_information_of_rawdata_sample(sample_number)

    def build_rectangular_data(self):
        if self.data_type != 'µXRF':
            self.build_laser_log_object()
            state_log = self.laserlog_object.build_sampleinlog_objects()
            self.gui.increase_progress(10)
            self.gui.increase_progress(30)
            self.build_rawdatasample_objects()
            self.gui.increase_progress(30)
            self.gui.increase_progress(30)
            self.gui.reset_progress()

    def export_data(self, sample, export_directory):

        if self.gui.well_data is None:
            self.gui.notifications.notification_error(header='Well Data Missing',
                                                      body='No Well data File has been imported.')
            self.gui.reset_progress()
            return
        if self.data_type == 'µXRF':
            test = pd.merge(self.gui.well_data, self.sample_rawdata_dictionary[sample], on='Well', how='inner')
            self.gui.well_data = test
        else:
            self.gui.increase_progress(25)
            for mass in self.RawdataSample_objects_dictionary[sample].mass_list:
                mass_dict = self.RawdataSample_objects_dictionary[sample].rawdata_dictionary[mass]
                if self.gui.widgets.background_sample_state.get() == 1:
                    average_background = int(np.average(mass_dict[self.gui.widgets.background_sample.get()]))
                else:
                    average_background = 0
                for well, value in mass_dict.items():
                    max_value = np.max(value)
                    max_index = np.where(value == max_value)[0][0]
                    value = np.delete(value, max_index)
                    average = int(np.average(value))-average_background
                    if average < 0 and average > -100:
                        average = 1
                    self.gui.well_data.loc[self.gui.well_data['Well'] == well, mass] = average
        if self.data_type == 'µXRF':
            columns_to_pass = ['Well', 'Cu Kα', 'As Kβ']
            Cu_column_name = 'Cu Kα'
            As_column_name = 'As Kβ'
            self.gui.well_data.fillna(0, inplace=True)
        else:
            columns_to_pass = ['Well', '65Cu | 65Cu', '75As | 75As.16O']
            Cu_column_name = '65Cu | 65Cu'
            As_column_name = '75As | 75As.16O'
        subset_df = self.gui.well_data[columns_to_pass]
        copper_outliers, arsenic_outliers, normal_outliers, base_group, merged_groups_df, len_dict = OutlierDetection.clustering_of_negative_samples(subset_df, Cu_column_name, As_column_name, data_type=self.data_type)


        self.gui.increase_progress(25)
        if self.data_type != 'µXRF':
            filename = self.RawdataSample_objects_dictionary[sample].name
            filename = filename.removesuffix('.csv')
        else:
            filename = sample
        export_filename = os.path.join(export_directory, filename + ".xlsx")

        writer = pd.ExcelWriter(export_filename, engine='xlsxwriter')
        self.gui.well_data.to_excel(writer, index=False, sheet_name='Data')
        self.gui.increase_progress(25)
        workbook = writer.book
        worksheet = writer.sheets['Data']

        outlier_format = workbook.add_format({'bg_color': '#FFCCCC'})  # Light red
        copper_format = workbook.add_format({'bg_color': '#CCCCFF'})  # Light blue
        arsenic_format = workbook.add_format({'bg_color': '#FFFFCC'})
        base_format = workbook.add_format({'bg_color': '#CCFFCC'})

        def col_to_excel(col_idx):
            """Convert zero-based column index to Excel-style letter."""
            letters = ''
            while col_idx >= 0:
                letters = chr(col_idx % 26 + 65) + letters
                col_idx = col_idx // 26 - 1
            return letters

        arsenic_col_letter = col_to_excel(self.gui.well_data.columns.get_loc(As_column_name))
        copper_col_letter = col_to_excel(self.gui.well_data.columns.get_loc(Cu_column_name))

        for idx, sample in enumerate(self.gui.well_data['Well'], start=2):
            if sample in normal_outliers.values:
                worksheet.write(f'{arsenic_col_letter}{idx}', self.gui.well_data.loc[idx - 2, As_column_name], outlier_format)
                worksheet.write(f'{copper_col_letter}{idx}', self.gui.well_data.loc[idx - 2, Cu_column_name], outlier_format)
            elif sample in copper_outliers.values:
                worksheet.write(f'{arsenic_col_letter}{idx}', self.gui.well_data.loc[idx - 2, As_column_name], copper_format)
                worksheet.write(f'{copper_col_letter}{idx}', self.gui.well_data.loc[idx - 2, Cu_column_name], copper_format)
            elif sample in arsenic_outliers.values:
                worksheet.write(f'{arsenic_col_letter}{idx}', self.gui.well_data.loc[idx - 2, As_column_name], arsenic_format)
                worksheet.write(f'{copper_col_letter}{idx}', self.gui.well_data.loc[idx - 2, Cu_column_name], arsenic_format)
            else:
                worksheet.write(f'{arsenic_col_letter}{idx}', self.gui.well_data.loc[idx - 2, As_column_name], base_format)
                worksheet.write(f'{copper_col_letter}{idx}', self.gui.well_data.loc[idx - 2, Cu_column_name], base_format)

        scatter_data_sheet = workbook.add_worksheet('Scatter_Plot')

        merged_groups_df.to_excel(writer, index=False, sheet_name='Scatter_Plot')
        chart = workbook.add_chart({'type': 'scatter'})

        len_of_series = len_dict['len_base_group']+1
        chart.add_series({
            'name': 'Group 1',
            'values': f"='Scatter_Plot'!$C$2:$C${len_of_series}",
            'categories': f"='Scatter_Plot'!$B$2:$B${len_of_series}",
            'marker': {'type': 'circle', 'size': 7, 'border': {'color': '#CCFFCC'}, 'fill': {'color': '#CCFFCC'}},
        })

        if len_dict['len_copper_skewed'] > 0:

            len_of_series = len_dict['len_copper_skewed'] + 1
            chart.add_series({
                'name': 'Group 2',
                'values': f"='Scatter_Plot'!$F$2:$F${len_of_series}",
                'categories': f"='Scatter_Plot'!$E$2:$E${len_of_series}",
                'marker': {'type': 'circle', 'size': 7, 'border': {'color': '#CCCCFF'}, 'fill': {'color': '#CCCCFF'}},
            })

        if len_dict['len_arsenic_skewed'] > 0:

            len_of_series = len_dict['len_arsenic_skewed'] + 1
            chart.add_series({
                'name': 'Group 3',
                'values': f"='Scatter_Plot'!$I$2:$I${len_of_series}",
                'categories': f"='Scatter_Plot'!$H$2:$H${len_of_series}",
                'marker': {'type': 'circle', 'size': 7, 'border': {'color': '#FFFFCC'}, 'fill': {'color': '#FFFFCC'}},
            })

        if len_dict['len_normal_outliers'] > 0:

            len_of_series = len_dict['len_normal_outliers'] + 1
            chart.add_series({
                'name': 'Group 4',
                'values': f"='Scatter_Plot'!$L$2:$L${len_of_series}",
                'categories': f"='Scatter_Plot'!$K$2:$K${len_of_series}",
                'marker': {'type': 'circle', 'size': 7, 'border': {'color': '#FFCCCC'}, 'fill': {'color': '#FFCCCC'}},
            })


        chart.set_title({'name': 'As vs Cu'})
        chart.set_x_axis({'name': "Intensity (65Cu+) / cps "})
        chart.set_y_axis({'name': 'Intensity (75As16O+) / cps'})
        chart.set_legend({'position': 'bottom'})
        scatter_data_sheet.insert_chart('I2', chart)
        writer.close()
        self.gui.increase_progress(25)
        self.gui.reset_progress()

    def rgba_to_hex(self, rgba):
        r, g, b, _ = rgba
        return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))

    def get_export_path(self):
        return self.gui.get_export_path()

    def get_separator_export(self):
        return self.gui.get_separator_export()
