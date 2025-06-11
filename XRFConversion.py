import os
import pandas as pd
import UXRFDataAnalysis

def process_spectra_in_folder(folder_path):
    """
    Processes spectra in a given folder by averaging the 'Impulse' values.
    Returns the averaged dataframe.
    """
    dataframes = []

    # Loop through all files in the folder
    for file in os.listdir(folder_path):
        if file.endswith(".xls"):  # Ensure it reads Excel 97-2003 files
            file_path = os.path.join(folder_path, file)
            # Read the Excel file, starting from row 21 (skip first 20 rows)
            df = pd.read_excel(file_path, skiprows=20, usecols=["Energie", "Impulse"])
            dataframes.append(df)

    if dataframes:
        # Merge all dataframes on 'Energie' and average the 'Impulse' values
        combined_df = pd.concat(dataframes)
        averaged_df = combined_df.groupby("Energie", as_index=False).mean()
        return averaged_df
    else:
        print(f"No valid spectra files found in folder: {folder_path}")
        return None

def traverse_and_process(folder_path):
    """
    Traverses the directory structure, processes spectra in the 'level 3' folders,
    and saves all averaged spectra as sheets in a single Excel file with charts.
    """
    spectra_data = {}  # To hold all averaged spectra and their names for the combined chart


    for level_2_folder in os.listdir(folder_path):
        level_2_path = os.path.join(folder_path, level_2_folder)
        if os.path.isdir(level_2_path):  # Check if it's a folder
            for level_3_folder in os.listdir(level_2_path):
                level_3_path = os.path.join(level_2_path, level_3_folder)
                if os.path.isdir(level_3_path):  # Check if it's a folder
                    print(f"Processing folder: {level_3_path}")
                    averaged_df = process_spectra_in_folder(level_3_path)
                    spectra_data[f'{level_2_folder}{level_3_folder}'] = averaged_df


    return spectra_data

def process_XRF_data(filepath,background_sample):
    level_1_folder = filepath
    spectra_data = traverse_and_process(level_1_folder)
    result_df = UXRFDataAnalysis.process_samples(spectra_data,
                                                    distance=10,
                                                    tolerance=0.2,
                                                 background_sample=background_sample)
    return result_df

