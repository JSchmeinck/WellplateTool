import pandas as pd
import numpy as np
import os
import tkinter as tk


def remove_on_blocks(df, column_name='Laser State'):
    indices_to_remove = []

    on_block_start = None
    on_block_end = None
    on_block_count = 0

    for index, row in df.iterrows():
        if row[column_name] == "On":
            if on_block_start is None:
                on_block_start = index
            on_block_end = index
            on_block_count += 1
        elif on_block_start is not None:
            if on_block_count > 2:
                indices_to_remove.extend(range(on_block_start + 2, on_block_end))
            on_block_start = on_block_end = on_block_count = None

    return df.drop(indices_to_remove)


class Importer:
    def __init__(self, gui):
        self.gui = gui

    def _load_csv_file(self, logfile, skip_rows=1):
        with open(logfile) as file:
            return pd.read_csv(file, skiprows=skip_rows, header=None)

    def _assign_columns(self, dataframe, column_names):
        try:
            dataframe.columns = column_names
        except ValueError:
            self.gui.notifications.notification_error(
                header="Data Type Error",
                body="Ihre Logfile-Daten passen nicht zum gewählten Laser-Typ.",
            )
            return None
        return dataframe

    def _extract_laser_data(self, dataframe, laser_type="Cetac G2+"):
        common_columns = [
            "Timestamp",
            "Sequence Number",
            "SubPoint Number",
            "Vertex Number",
            "Comment",
            "X(um)",
            "Y(um)",
            "Intended X(um)",
            "Intended Y(um)",
            "Scan Velocity (um/s)",
            "Laser State",
            "Laser Rep. Rate (Hz)",
            "Spot Type",
            "Spot Size (um)",
        ]

        if laser_type == "Cetac G2+":
            specific_columns = ["Spot Type", "Spot Size", "Spot Angle", "MFC1", "MFC2"]
        else:
            specific_columns = []
        column_names = common_columns + specific_columns
        dataframe = self._assign_columns(dataframe, column_names)
        if dataframe is None:
            return None

        return dataframe

    def import_laser_logfile(self, logfile, laser_type, rectangular_data_calculation):
        logfile_dataframe = self._load_csv_file(logfile)
        logfile_dataframe = self._extract_laser_data(logfile_dataframe, laser_type)
        if logfile_dataframe is None:
            return None

        if rectangular_data_calculation:
            return self._process_rectangular_data(logfile_dataframe, laser_type)

        return logfile_dataframe

    def _process_rectangular_data(self, dataframe, laser_type):
        if "Cetac G2+" in laser_type:
            dataframe["Processed Column"] = dataframe["X(um)"] * dataframe["Y(um)"]
        else:
            dataframe = remove_on_blocks(dataframe)
        return dataframe

    def import_sample_file(self, data_type, synchronized):
        sample_rawdata_dictionary = {}
        for i, filepath in enumerate(self.gui.list_of_files):
            with open(filepath) as file:
                skip_rows = 13 if data_type == "iCap TQ (Daisy)" and synchronized else 2
                df = pd.read_csv(file, sep=self.gui.get_separator_import(), skiprows=skip_rows)
                sample_rawdata_dictionary[self.gui.filename_list[i]] = df
        return sample_rawdata_dictionary

    def import_well_data(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            self.gui.widgets.lbl_file.config(text=file_name)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            self.gui.experiment.well_information = df