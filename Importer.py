import pandas as pd
import numpy as np
import os
import tkinter as tk

def filter_laser_shots(df):
    # Initialize an empty list to collect the rows to keep
    rows_to_keep = []

    # Track the current sample's start row
    sample_start_idx = None
    total_rows = len(df)

    # Loop through the dataframe to process each sample
    for i in range(total_rows):
        # If we find a new sample (non-empty Name column), process the previous sample if necessary
        if pd.notna(df.at[i, 'Comment']):
            if sample_start_idx is not None:
                # Handle the previous sample, add the start row, first shot, and last shot
                first_laser_shot_idx = sample_start_idx + 2  # First laser shot row
                last_laser_shot_idx = sample_start_idx + 2 + 3 * 19  # Last laser shot row (19th laser shot)

                # Keep the sample start row, first shot and last shot rows
                rows_to_keep.append(sample_start_idx)
                rows_to_keep.append(first_laser_shot_idx)
                rows_to_keep.append(first_laser_shot_idx + 1)
                rows_to_keep.append(first_laser_shot_idx + 1)
                rows_to_keep.append(last_laser_shot_idx + 1)
                rows_to_keep.append(last_laser_shot_idx + 2)

            # Update the sample_start_idx to the new sample start
            sample_start_idx = i

    # Make sure to process the last sample after the loop
    if sample_start_idx is not None:
        first_laser_shot_idx = sample_start_idx + 2  # First laser shot row
        last_laser_shot_idx = sample_start_idx + 2 + 3 * 19  # Last laser shot row (19th laser shot)

        # Keep the sample start row, first shot and last shot rows
        rows_to_keep.append(sample_start_idx)
        rows_to_keep.append(first_laser_shot_idx)
        rows_to_keep.append(first_laser_shot_idx + 1)
        rows_to_keep.append(first_laser_shot_idx + 1)
        rows_to_keep.append(last_laser_shot_idx + 1)
        rows_to_keep.append(last_laser_shot_idx + 2)

    # Filter the dataframe by the rows to keep
    filtered_df = df.iloc[rows_to_keep].reset_index(drop=True)

    column_name = 'Intended X(um)'
    column_index = filtered_df.columns.get_loc(column_name)

    # Step 1: Reset the values in the 'Intended X(um)' column to NaN
    filtered_df[column_name] = np.nan

    # Step 2: Update the fourth and fifth rows of each set of 6 rows to 1
    num_rows = len(filtered_df)
    rows_per_set = 6
    for i in range(0, num_rows, rows_per_set):
        if i + 4 < num_rows:  # Ensure within bounds
            filtered_df.at[i + 3, column_name] = 1  # Fourth row in the set
        if i + 5 < num_rows:  # Ensure within bounds
            filtered_df.at[i + 4, column_name] = 1  # Fifth row in the set

    return filtered_df


def remove_on_blocks(df, column_name='Laser State'):
    indices_to_remove = []

    # Initialize variables to track consecutive "On" blocks
    on_block_start = None
    on_block_end = None
    on_block_count = 0

    # Iterate over the DataFrame
    for index, row in df.iterrows():
        if row[column_name] == "On":
            if on_block_start is None:
                on_block_start = index
            on_block_end = index
            on_block_count += 1
        elif on_block_start is not None:
            # Keep the first two rows and the last row within the "On" block
            if on_block_count > 2:
                indices_to_remove.extend(list(range(on_block_start + 2, on_block_end)))
            on_block_start = None
            on_block_end = None
            on_block_count = 0

    # Remove identified rows
    df = df.drop(indices_to_remove)

    return df


class Importer:
    def __init__(self, gui):
        self.gui = gui

    def import_laser_logfile(self, logfile, laser_type, rectangular_data_calculation, iolite_file=False, logfile_viewer=False, wellplate_singleshots=True):
        if laser_type == 'Cetac G2+':
            if rectangular_data_calculation is False:
                with open(logfile) as file:
                    logfile_dataframe = pd.read_csv(file, skiprows=1, header=None)
                logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                             'Comment',
                                             'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                             'Scan Velocity (um/s)',
                                             'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)',
                                             'Spot Type', 'Spot Size', 'Spot Angle', 'MFC1', 'MFC2']
                return logfile_dataframe
            else:
                with open(logfile) as file:
                    iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
                iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                            'Comment',
                                            'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                            'Scan Velocity (um/s)',
                                            'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)',
                                            'Spot Type', 'Spot Size', 'Spot Angle', 'MFC1', 'MFC2']
                logfile_dictionary = {}

                scan_speed_array = iolite_dataframe['Scan Velocity (um/s)'].dropna().values
                scan_speed_array[1::2] = np.nan

                pattern_number_array = iolite_dataframe['Sequence Number'].dropna().values
                pattern_number_array = pattern_number_array.repeat(2)
                run_queue_order_array = pattern_number_array.copy()
                pattern_number_array[1::2] = np.nan

                run_queue_order_array = run_queue_order_array - 1
                run_queue_order_array[1::2] = np.nan

                name_array = iolite_dataframe['Comment'].dropna().values
                name_array = name_array.repeat(2)
                name_array[1::2] = np.nan

                type_array = iolite_dataframe['Spot Type'].to_numpy()
                type_array = type_array[:, 0]
                type_array = type_array[0::7]
                type_array = type_array.repeat(2)
                type_array[1::2] = np.nan

                spotsize_array = iolite_dataframe['Spot Size (um)'].to_numpy()
                spotsize_array = spotsize_array[0::7]
                spotsize_array = spotsize_array.repeat(2)
                spotsize_array = spotsize_array.astype(float)
                spotsize_array[1::2] = np.nan

                x_array = iolite_dataframe['Intended X(um)'].dropna().values
                y_array = iolite_dataframe['Intended Y(um)'].dropna().values

                logfile_dictionary['Pattern #'] = pattern_number_array
                logfile_dictionary['Name'] = name_array
                logfile_dictionary['Type'] = type_array
                logfile_dictionary['Run Queue Order'] = run_queue_order_array
                logfile_dictionary['Scan Speed(Î¼m/sec)'] = scan_speed_array
                logfile_dictionary['X(um)'] = x_array
                logfile_dictionary['Y(um)'] = y_array
                logfile_dictionary['Spotsize'] = spotsize_array

                logfile_dataframe = pd.DataFrame(logfile_dictionary)

                return logfile_dataframe

        if laser_type == 'ImageBIO 266':
            if iolite_file and rectangular_data_calculation:
                with open(logfile) as file:
                    iolite_dataframe = pd.read_csv(file, skiprows=1, header=None)
                try:
                    iolite_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']
                except ValueError:
                    self.gui.notifications.notification_error(header='Data Type Error',
                                                              body='Your Logfile Data does not match your chosen Laser Type')
                    return False

                if wellplate_singleshots is True:
                    iolite_dataframe = filter_laser_shots(df=iolite_dataframe)
                else:
                    iolite_dataframe = remove_on_blocks(df=iolite_dataframe)

                iolite_dataframe['Comment'] = iolite_dataframe['Comment'].str.replace('_', '', regex=False)

                logfile_dictionary = {}

                scan_speed_array = iolite_dataframe['Scan Velocity (um/s)'].dropna().values
                scan_speed_array[1::2] = np.nan

                pattern_number_array = iolite_dataframe['Sequence Number'].dropna().values
                pattern_number_array = pattern_number_array.repeat(2)
                run_queue_order_array = pattern_number_array.copy()
                pattern_number_array[1::2] = np.nan

                run_queue_order_array = run_queue_order_array - 1
                run_queue_order_array[1::2] = np.nan

                name_array = iolite_dataframe['Comment'].dropna().values
                name_array = name_array.repeat(2)
                name_array[1::2] = np.nan

                type_array = iolite_dataframe['Laser State'].to_numpy()
                type_array = type_array[0::6]
                type_array = type_array.repeat(2)
                type_array[1::2] = np.nan

                logfile_dictionary['Pattern #'] = pattern_number_array
                logfile_dictionary['Name'] = name_array



                logfile_dataframe = pd.DataFrame(logfile_dictionary)

                return logfile_dataframe

            if iolite_file and rectangular_data_calculation is False:
                with open(logfile) as file:
                    logfile_dataframe = pd.read_csv(file, skiprows=1, header=None)
                try:
                    logfile_dataframe.columns = ['Timestamp', 'Sequence Number', 'SubPoint Number', 'Vertex Number',
                                                 'Comment',
                                                 'X(um)', 'Y(um)', 'Intended X(um)', 'Intended Y(um)',
                                                 'Scan Velocity (um/s)',
                                                 'Laser State', 'Laser Rep. Rate (Hz)', 'Spot Type', 'Spot Size (um)']

                    logfile_dataframe = remove_on_blocks(df=logfile_dataframe)
                    if wellplate_singleshots is True:
                        logfile_dataframe = filter_laser_shots(df=logfile_dataframe)
                    logfile_dataframe['Comment'] = logfile_dataframe['Comment'].str.replace('_', '', regex=False)

                except ValueError:
                    self.gui.notifications.notification_error(header='Data Type Error',
                                                              body='Your Logfile Data does not match your chosen Laser Type')
                    return False
                return logfile_dataframe

            else:
                try:
                    with open(logfile) as f:
                        # pattern_dataframe = pd.read_csv(f, skipinitialspace=True).fillna('Faulty Line')

                        logfile_dataframe = pd.read_csv(f, usecols=['Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)
                except:
                    with open(logfile) as f:
                        logfile_dataframe = pd.read_csv(f, usecols=['ï»¿Pattern #', 'Name', 'Type', 'Run Queue Order',
                                                                    'Grid Spacing(Î¼m)', 'Scan Speed(Î¼m/sec)', 'X(um)',
                                                                    'Y(um)'], index_col=False)
                return logfile_dataframe


    def import_sample_file(self, data_type, synchronized):
        sample_rawdata_dictionary: dict = {}
        if data_type == 'iCap TQ (Daisy)':
            for n, m in enumerate(self.gui.list_of_files):
                if synchronized:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.gui.get_separator_import(),
                                                       skiprows=13)
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = df
                    break
                else:
                    with open(m) as f:
                        # First 15 lines have to be skipped (in Qtegra files)
                        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=f,
                                                       sep=self.gui.get_separator_import())
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = df

            return sample_rawdata_dictionary

        if data_type == 'Agilent 7900':
            # Loop through the imported directorys one by one
            for n, m in enumerate(self.gui.list_of_files):
                individual_lines_dictionary = {}
                directory = os.fsencode(m)
                # Loop trough the files inside the directory
                for ticker, file in enumerate(os.listdir(directory)):
                    filename = os.fsdecode(file)
                    # Only use the files that are csv data
                    if filename.endswith(".csv"):
                        with open(f'{m}/{filename}') as f:
                            df = pd.read_csv(filepath_or_buffer=f,
                                             sep=self.gui.get_separator_import(),
                                             skiprows=3,
                                             skipfooter=1,
                                             engine='python')
                        individual_lines_dictionary[f'Line_{ticker + 1}'] = df
                    sample_rawdata_dictionary[f'{self.gui.filename_list[n]}'] = individual_lines_dictionary

            return sample_rawdata_dictionary

        if data_type == 'EIC':
            for n, m in enumerate(self.gui.list_of_files):
                with open(m) as f:
                    df: pd.DataFrame = pd.read_csv(f, sep=self.gui.get_separator_import(), skiprows=2, engine='python')
                df.drop(columns=[df.columns[-1]], inplace=True)
                sample_rawdata_dictionary, list_of_unique_masses_in_file, time_data_sample = self.gui.synchronizer.get_data(sample_name='Full Data')

            return sample_rawdata_dictionary

    def import_well_data(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            file_name = os.path.splitext(os.path.basename(file_path))[0]  # Extract filename without extension
            self.gui.widgets.lbl_file.config(text=file_name)
            # Read the file and display its content
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                df['Well'] = df['Well'].str.replace('_', '', regex=False)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
                df['Well'] = df['Well'].str.replace('_', '', regex=False)
            self.gui.experiment.well_information = df


        