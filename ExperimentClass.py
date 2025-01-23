import os
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np
import re
from tkinter import messagebox
import LaserlogClass
import RawdataSampleClass
import keyboard
import tkinter as tk
from tkinter import ttk
from decimal import Decimal
import string
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import xlsxwriter


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
        self.well_information = None
        self.rectangles_dictionary = {}

        self.putative_value_arsenic = None
        self.decider_value_arsenic = None
        self.putative_value_copper = None
        self.decider_value_copper = None

    def build_laser_log_object(self):

        # Filter rows
        filtered_df = self.raw_laser_logfile_dataframe
        filtered_df = filtered_df.reset_index(drop=True)
        name = os.path.basename(self.logfile_filepath).removesuffix('.csv')
        self.laserlog_object = LaserlogClass.Laserlog(experiment=self,
                                                      clean_laserlog_dataframe=filtered_df,
                                                      name=name)


    def build_rawdatasample_objects(self):
        sample_counter = 1
        if self.synchronized:
            for sample_name, sample_rawdata_dataframe in self.sample_rawdata_dictionary.items():
                rawdata_extracted_masses_dictionary = {}
                synchronized_data, list_of_unique_masses_in_file, time_data_sample = self.gui.synchronizer.get_data(
                    sample_name=sample_name)

                list_of_col_names = []
                self.gui.widgets.choose_data_combobox['values'] = list_of_unique_masses_in_file
                for k, i in enumerate(list_of_unique_masses_in_file):
                    extracted_sample_column_dictionary = {}
                    # Iterate over the columns
                    for col in synchronized_data.columns:
                        if col != 'Unnamed: 2':
                            if k == 0:
                                list_of_col_names.append(col)
                            filtered_values = synchronized_data[synchronized_data['Unnamed: 2'] == i][col].values

                            # Convert the result to a NumPy array
                            extracted_values = np.array(filtered_values)

                            extracted_array = extracted_values.astype(float)

                            # Filter out non-numeric values (strings, NaNs, etc.)
                            extracted_array = extracted_values[~np.isnan(extracted_array)]
                            # Convert the filtered values to a NumPy array

                            # Add the extracted array to the dictionary
                            extracted_array = extracted_array.astype(float)


                            extracted_sample_column_dictionary[col] = extracted_array
                            extracted_array = 0
                    rawdata_extracted_masses_dictionary[i] = extracted_sample_column_dictionary
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 sample_number=f'Sample_{sample_counter}',
                                                                 column_names=list_of_col_names,
                                                                 mass_list=list_of_unique_masses_in_file)
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

        elif self.data_type == 'iCap TQ (Daisy)':
            for sample_name, sample_rawdata_dataframe in self.sample_rawdata_dictionary.items():
                rawdata_extracted_masses_dictionary = {}
                mass_options: np.ndarray = sample_rawdata_dataframe['Unnamed: 2'].unique()
                mass_options_clean: np.ndarray = np.delete(mass_options, [0])
                mass_options_list: list = list(mass_options_clean)
                # Determine dwell times for each element and the total cycle time for each sample


                list_of_col_names = []
                for k, i in enumerate(mass_options_list):
                    extracted_sample_column_dictionary = {}
                    # Iterate over the columns
                    for col in sample_rawdata_dataframe.columns:
                        if col.startswith('Sample'):
                            if k == 0:
                                list_of_col_names.append(col)
                            sample_col = sample_rawdata_dataframe[col]
                            identifier_col_2 = sample_rawdata_dataframe['Unnamed: 2']
                            identifier_col_3 = sample_rawdata_dataframe['Unnamed: 3']
                            # Find the indices where both identifiers match
                            # indices = np.where((identifier_col_2 == i) & (identifier_col_3 == 'Y'))[0]
                            list1 = np.where((identifier_col_2 == i))[0]
                            list2 = np.where((identifier_col_3 == 'Y'))[0]
                            indices = np.intersect1d(list1, list2)
                            # Extract the corresponding values from the sample column
                            extracted_values = sample_col.iloc[indices]
                            # Filter out non-numeric values (strings, NaNs, etc.)
                            extracted_values = extracted_values.loc[
                                extracted_values.apply(lambda x: pd.to_numeric(x, errors='coerce')).notnull()]
                            # Convert the filtered values to a NumPy array
                            extracted_array = extracted_values.astype(float).to_numpy()
                            # Add the extracted array to the dictionary

                            extracted_sample_column_dictionary[col] = extracted_array
                            extracted_array = 0
                    rawdata_extracted_masses_dictionary[i] = extracted_sample_column_dictionary
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 sample_number=f'Sample_{sample_counter}',
                                                                 column_names=list_of_col_names,
                                                                 mass_list=mass_options_list)
                sample_counter += 1
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

        elif self.data_type == 'Agilent 7900':
            for sample_name, sample_rawdata_dictionary in self.sample_rawdata_dictionary.items():
                rawdata_extracted_masses_dictionary = {}
                sample_dataframe: pd.DataFrame = sample_rawdata_dictionary['Line_1']
                header_list = list(sample_dataframe)
                mass_options_list = header_list[1:]

                list_of_column_names = []
                for line, raw_dataframe in sample_rawdata_dictionary.items():
                    for mass in mass_options_list:
                        rawdata_extracted_masses_dictionary[mass][f'{line}'] = raw_dataframe[mass].to_numpy()
                    list_of_column_names.append(line)

                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 sample_number=f'Sample_{sample_counter}',
                                                                 column_names=list_of_column_names,
                                                                 mass_list=mass_options_list)
                sample_counter += 1
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

    def pass_sample_logfile_information(self, sample_number: str):
        return self.laserlog_object.get_log_information_of_rawdata_sample(sample_number)

    def build_rectangular_data(self):
        self.build_laser_log_object()
        self.gui.increase_progress(10)
        state_log = self.laserlog_object.build_sampleinlog_objects()
        if state_log is False:
            self.gui.notifications.notification_error(header='Logfile Error',
                                                      body='Logfile shows new pattern starting without previous '
                                                           'pattern being completed by end statement')
            self.gui.reset_progress()
            return
        self.gui.increase_progress(30)
        self.build_rawdatasample_objects()
        self.gui.increase_progress(30)
        #self.calculate_decider_values()
        self.gui.increase_progress(30)

    def build_laser_ablation_times(self):
        # Step 1
        self.build_laser_log_object()
        # Step 2
        state_log = self.laserlog_object.build_sampleinlog_objects()
        if state_log is False:
            self.gui.notifications.notification_error(header='Match Error',
                                                      body='Unable to match laser logfile and rawdata files!')
            self.gui.reset_progress()
            return
        # Step 3
        state = self.laserlog_object.build_laser_pattern_duration_sheet()
        if state is False:
            self.gui.notifications.notification_error(header='Export Path Error',
                                                      body='No Directory for the export of the pattern duration file has been chosen!')
            self.gui.reset_progress()
            return

    def match_log_and_sample(self, match_by_line_count=False):
        length_of_sample_dictionary = self.laserlog_object.build_lengh_of_sample_dictionary()
        samples_in_log = self.laserlog_object.get_sampleinlog_objects_dictionary()
        if match_by_line_count is False:
            for k, i in enumerate(self.RawdataSample_objects_dictionary.values()):
                i.set_sample_in_log(samples_in_log[f'Sample_{k + 1}'])
                amount_of_log_lines = length_of_sample_dictionary[samples_in_log[f'Sample_{k + 1}']]
                amount_of_rawdata_lines = i.get_amount_of_lines()
                if amount_of_rawdata_lines == amount_of_log_lines:
                    pass
                else:
                    decider = self.gui.notifications.notification_yesno(header='Logfile and and Rawdata match issue',
                                                                        body='The amount of ablated lines dont match '
                                                                             'between the laser'
                                                                             'logfile and the predetermined rawdata '
                                                                             'file.'
                                                                             'Do you want to use automatic assignment? '
                                                                             ''
                                                                             '(This only works if all of your samples '
                                                                             'have a unique'
                                                                             'amount of ablated lines)')
                    if decider is True:
                        self.match_log_and_sample(match_by_line_count=decider)
                        return True
                    if decider is False:
                        return False

        if match_by_line_count is True:
            for i in self.RawdataSample_objects_dictionary.values():
                for laserlog_object, amount_of_lines in length_of_sample_dictionary.items():
                    amount_of_samples = i.get_amount_of_lines()
                    if amount_of_samples == amount_of_lines:
                        i.set_sample_in_log(laserlog_object)


    def calculate_decider_values(self):

        # This is the calculation of the blank value for books that dont contain arsenic pigments and were also not near
        # books containing these pigments. Therefore they should only account for the natural backround of
        # arsenic in historic book bindings.
        average_truebookblank_arsenic = self.well_information.loc[
            self.well_information['Well'].isin(['A2', 'A3', 'A4', 'A8', 'A11', 'B11', 'F7', 'F9', 'G6', 'H1']), '75As | 75As.16O'].mean()
        std_dev_truebookblank_arsenic = self.well_information.loc[
            self.well_information['Well'].isin(['A2', 'A3', 'A4', 'A8', 'A11', 'B11', 'F7', 'F9', 'G6', 'H1']), '75As | 75As.16O'].std()

        self.putative_value_arsenic = average_truebookblank_arsenic + 3 * std_dev_truebookblank_arsenic

        # This is the calculation of the blank value for Book 13. This book was chosen as the true decider for
        # arsenic pigments, as this also accounts for effects like contamination from nearby books and also
        # contamination by readers. That this book doesnt contain arsenic pigments was shown using µXRF measurements
        average_bookblank_arsenic = self.well_information.loc[self.well_information['Well'].isin(
            ['E7', 'E8', 'E9', 'G8', 'G9', 'H5', 'H6', 'H10', 'H11']), '75As | 75As.16O'].mean()
        std_dev_bookblank_arsenic = self.well_information.loc[self.well_information['Well'].isin(
            ['E7', 'E8', 'E9', 'G8', 'G9', 'H5', 'H6', 'H10', 'H11']), '75As | 75As.16O'].std()

        self.decider_value_arsenic = average_bookblank_arsenic + 3 * std_dev_bookblank_arsenic


        #Same calculations for copper

        average_truebookblank_copper = self.well_information.loc[
            self.well_information['Well'].isin(['A2', 'A3', 'A4', 'A8', 'A11', 'B11', 'F7', 'F9', 'G6', 'H1']), '65Cu | 65Cu'].mean()
        std_dev_truebookblank_copper = self.well_information.loc[
            self.well_information['Well'].isin(['A2', 'A3', 'A4', 'A8', 'A11', 'B11', 'F7', 'F9', 'G6', 'H1']), '65Cu | 65Cu'].std()

        self.putative_value_copper = average_truebookblank_copper + 3 * std_dev_truebookblank_copper

        # This is the calculation of the blank value for Book 13. This book was chosen as the true decider for
        # arsenic pigments, as this also accounts for effects like contamination from nearby books and also
        # contamination by readers. That this book doesnt contain arsenic pigments was shown using µXRF measurements
        average_bookblank_copper = self.well_information.loc[self.well_information['Well'].isin(
            ['E7', 'E8', 'E9', 'G8', 'G9', 'H5', 'H6', 'H10', 'H11']), '65Cu | 65Cu'].mean()
        std_dev_bookblank_copper = self.well_information.loc[self.well_information['Well'].isin(
            ['E7', 'E8', 'E9', 'G8', 'G9', 'H5', 'H6', 'H10', 'H11']), '65Cu | 65Cu'].std()

        self.decider_value_copper = average_bookblank_copper + 3 * std_dev_bookblank_copper

    def export_data(self, sample, export_directory):
        for mass in self.RawdataSample_objects_dictionary[sample].mass_list:
            mass_dict = self.RawdataSample_objects_dictionary[sample].rawdata_dictionary[mass]
            for well, value in mass_dict.items():
                percentile_90 = np.percentile(value, 90)

                # Filter out the top 10% values
                filtered_arr = value[value <= percentile_90]
                average = int(np.average(filtered_arr))
                self.well_information.loc[self.well_information['Well'] == well, mass] = average


        filename = self.RawdataSample_objects_dictionary[sample].name
        filename = filename.removesuffix('.csv')
        export_filename = os.path.join(export_directory, filename + ".xlsx")
        #self.well_information.to_excel(export_filename, index=False)

        # Write DataFrame to Excel file

        writer = pd.ExcelWriter(export_filename, engine='xlsxwriter')
        self.well_information.to_excel(writer, index=False, sheet_name='Sheet1')

        # Apply cell formatting
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Close the Pandas Excel writer and output the Excel file
        writer.close()



    def show_data(self, sample, analyte):
        window = self.gui.create_new_window(analyte)
        self.rectangles_dictionary = {}
        data = self.RawdataSample_objects_dictionary[sample].get_data(analyte)
        arsenic_data = self.RawdataSample_objects_dictionary[sample].get_data('75As | 75As.16O')
        copper_data = self.RawdataSample_objects_dictionary[sample].get_data('65Cu | 65Cu')
        frame_for_canvas = ttk.Frame(master=window, width=1000, height=700)
        canvas = tk.Canvas(master=frame_for_canvas, width=window.winfo_width(),
                           height=window.winfo_height())
        mean_data_dictionary = {}
        rectangles_dictionary = {}

        label_width = 50
        label_height = 50
        cell_width = 0
        cell_height = 0
        padding = 4

        mean_data_label = ttk.Label(master=window, text='')

        try:
            custom_cmap = mpl.colors.LinearSegmentedColormap.from_list(name='AK Karst', colors=['black', '#AF00FF', '#0000FF',
                                                                                        '#007FFF', '#00FFFF', '#00FF7F',
                                                                                        '#00FF00', '#7FFF00', '#FFFF00',
                                                                                        '#FFC800', '#FF0000'])
            plt.colormaps.register(cmap=custom_cmap)
        except ValueError:
            pass

        try:
            custom_cmap = mpl.colors.LinearSegmentedColormap.from_list(name='Yellows',
                                                                           colors=['white', '#f5e216'])
            plt.colormaps.register(cmap=custom_cmap)
        except ValueError:
            pass

        chosen_cmap = self.gui.options_menu.colormap_combobox.get()
        colormap = mpl.colormaps[chosen_cmap]
        averages = []
        for sample in data.values():
            average = np.average(sample)
            averages.append(average)
        absolute_max = int(max(averages))
        absolute_min = 0

        if self.gui.options_menu.min_value.get() != 'None':
            absolute_min = int(self.gui.options_menu.min_value.get())
        if self.gui.options_menu.max_value.get() != 'None':
            absolute_max = int(self.gui.options_menu.max_value.get())

        self.gui.options_menu.min_value.set(str(absolute_min))
        self.gui.options_menu.max_value.set(str(absolute_max))

        list_of_wells = []

        wellplate_letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        wellplate_numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]

        for row_number, well_letter in enumerate(wellplate_letters):
            for column_number, well_number in enumerate(wellplate_numbers):
                if f'{well_letter}{well_number}' in data.keys():
                    well_data = data[f'{well_letter}{well_number}']
                    mean_data_dictionary[f'{well_letter}{well_number}'] = np.average(well_data)
                    list_of_wells.append(f'{well_letter}{well_number}')
                elif f'{well_letter}_{well_number}' in data.keys():
                    well_data = data[f'{well_letter}_{well_number}']
                    mean_data_dictionary[f'{well_letter}{well_number}'] = np.average(well_data)
                    list_of_wells.append(f'{well_letter}{well_number}')
                    underscores = True
                else:
                    print(f'Well {well_letter}{well_number} not in Data')

        frame_width = 1200
        frame_height = 800

        canvas_width = frame_width*0.8
        canvas_height = frame_height*1

        canvas.config(width=canvas_width, height=canvas_height)


        #if self.sample.get_wellplate_type() == '384':
            #self.cell_width = ((canvas_width-100) - (24 - 1) * self.padding) // 24
            #self.cell_height = ((canvas_height-400) - (12 - 1) * self.padding) // 12
        #if self.sample.get_wellplate_type() == '96':
        cell_width = ((canvas_width-100) - (24 - 1) * padding * 0.8) // 12
        cell_height = ((canvas_height-400) - (12 - 1) * padding) // 6

        for row_number, well_letter in enumerate(wellplate_letters):
            for column_number, well_number in enumerate(wellplate_numbers):
                well = f'{well_letter}{well_number}'
                if well in list_of_wells:
                    mean_raw_data_of_well = mean_data_dictionary[well]
                    norm_value = mean_raw_data_of_well / absolute_max  # Normalize the value to [0, max_malue] for colormap
                    color = self.rgba_to_hex(colormap(norm_value))
                    x0 = column_number * (cell_width + padding) + label_width
                    y0 = row_number * (cell_height + padding) + label_height
                    x1 = x0 + cell_width
                    y1 = y0 + cell_height
                    rectangle = canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='black')
                    self.rectangles_dictionary[well] = rectangle
                else:
                    pass

        for col in range(len(wellplate_numbers)):
            x = col * (cell_width + padding) + label_width + cell_width // 2
            y = label_height // 2
            canvas.create_text(x, y, text=str(col + 1), font=("Helvetica", int(frame_height*0.02)))

        # Draw row names
        for row in range(len(wellplate_letters)):
            x = label_width // 2
            y = row * (cell_height + padding) + label_height + cell_height // 2
            canvas.create_text(x, y, text=string.ascii_uppercase[row], font=("Helvetica", int(frame_height*0.02)))

        frame_for_canvas.grid(row=0, column=0)
        frame_for_canvas.grid_propagate(False)

        canvas.grid(row=0, column=0, pady=(frame_height*0.1), padx=(frame_width*0.05))
        mean_data_label.config(font=("Helvetica", int(frame_height*0.02)))
        mean_data_label.grid(row=1, column=0, columnspan=2, sticky='s', pady=(0, 200))

        # Colorbar
        colorbar_frame = tk.Frame(master=window, width=150, height=frame_height*0.9)
        colorbar_frame.grid_propagate(False)
        colorbar_frame.grid(row=0, column=1)
        fig = plt.figure(figsize=((frame_width*0.4) / 100, (frame_height*0.8) / 100), dpi=100)
        fig.patch.set_facecolor('#f0f0f0')
        ax = fig.add_axes([0, 0.1, 0.08, 0.8])
        norm = mpl.colors.Normalize(vmin=absolute_min, vmax=absolute_max)
        cb = mpl.colorbar.ColorbarBase(ax, orientation='vertical', cmap=chosen_cmap, norm=norm, label=f'Intensity ({analyte}) / cps')
        canvas_colorbar = FigureCanvasTkAgg(fig, master=colorbar_frame)
        canvas_colorbar.get_tk_widget().grid(row=0, column=0)
        canvas_colorbar.draw()

        #canvas.bind("<Motion>", self.show_value)
        #canvas.bind("<Button-1>", self.show_stats)
        #keyboard.add_hotkey('space', lambda: self.freeze_infotable())



    def rgba_to_hex(self, rgba):
        r, g, b, _ = rgba
        return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))

    def get_export_path(self):
        return self.gui.get_export_path()

    def get_separator_export(self):
        return self.gui.get_separator_export()
