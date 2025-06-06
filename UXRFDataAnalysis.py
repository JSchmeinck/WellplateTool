import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.signal import peak_widths
import scipy
import matplotlib.pyplot as plt
import os

def detect_peaks(intensity, distance):
    """
    Detect peaks in an intensity array.
    :param intensity: array of spectra data
    :param distance: distance between a detected peak and the next peak
    :return: Position of the peaks in the intensity array, their properties and their start and end positions in the intensity array.
    """

    peaks, properties = find_peaks(intensity, distance=distance, prominence=10, width=4, wlen=27)
    results_half = peak_widths(intensity, peaks, rel_height=0.5)
    left_ips = results_half[2].astype(int)
    right_ips = results_half[3].astype(int)
    return peaks, properties, left_ips, right_ips

def integrate_peak(energy, intensity, left_ips, right_ips, background_sample, sample_dict):
    """
    Calculates peak areas for peaks found by detect_peaks function.
    :param energy: x data of spectra.
    :param intensity: array of spectra y data.
    :param left_ips: start positions of peaks in intensity array.
    :param right_ips: end positions of peaks in intensity array.
    :param background_sample: if selected, spectra data is background corrected. This is the position of the background sample on the well plate.
    :param sample_dict: dictionary of all spectra data.
    :return: The area of the currently selected peak in the spectrum.
    """
    if background_sample is not None:
        background_df = sample_dict[background_sample]
        background_intensity = background_df['Impulse'].to_numpy()
        corrected_intensity = intensity - background_intensity
        corrected = corrected_intensity[left_ips:right_ips]
    else:
        baseline = np.linspace(intensity[left_ips], intensity[right_ips - 1], right_ips - left_ips)
        corrected = intensity[left_ips:right_ips] - baseline
    area = scipy.integrate.simpson(corrected, energy[left_ips:right_ips])
    return area

def assign_peak(peak_energy, tolerance=0.09):
    """
    Assigns peaks to emissions of elements based on their energy value.
    :param peak_energy: peak x value.
    :param tolerance: tolerance allowed between peak-energy and element emission line.
    :return:
    """
    emission_lines = {
        'As': [(10.53, 'Kα'), (11.72, 'Kβ')],
        'Cu': [(8.05, 'Kα'), (8.90, 'Kβ')],
        'Hg': [(9.99, 'Lα'), (11.82, 'Lβ')],
        'Pb': [(10.55, 'Lα'), (12.61, 'Lβ')],
        'S':  [(2.31, 'Kα')]
    }
    assignments = []
    for element, lines in emission_lines.items():
        for energy_value, emission_type in lines:
            if abs(peak_energy - energy_value) <= tolerance:
                assignments.append(f"{element} {emission_type}")
    return assignments

def process_sample(sample_name, df, background_sample, sample_dict, distance=5, tolerance=0.09, plot=False):
    """
        Process a single µXRF sample.

        For copper and arsenic the routine requires that both the Kα and Kβ peaks are detected.
        If one of the pair is missing, both integrated areas for that element will be set to NaN.

        Parameters:
          sample_name: name of the sample
          df         : DataFrame with 'energy' and 'intensity' columns
          height_threshold, distance, tolerance, fraction: parameters for peak detection/integration

        Returns:
          A dictionary containing the sample name and integrated areas for each emission line.
        """
    energy = df['Energie'].to_numpy()
    intensity = df['Impulse'].to_numpy()
    folder_path = r'D:\M4 Tornado\CSV3'
    file_path = os.path.join(folder_path, f'{sample_name}.csv')
    np.savetxt(file_path, np.column_stack((energy, intensity)), delimiter=";", header="Energie;Impulse", comments='',
               fmt='%.6f')
    peaks, properties, left_ips, right_ips = detect_peaks(intensity=intensity, distance=distance)
    ambiguous_AsPb = []

    emission_areas = {}
    peak_annotations = []
    for peak, left, right in zip(peaks, left_ips, right_ips):
        peak_energy = energy[peak]
        area = integrate_peak(energy, intensity, left, right, background_sample=background_sample, sample_dict=sample_dict)
        assignments = assign_peak(peak_energy, tolerance)
        peak_annotations.append({
            'energy': peak_energy,
            'intensity': intensity[peak],
            'area': area,
            'assignments': assignments,
            'left': left,
            'right': right
        })
        if "As Kα" in assignments and "Pb Lα" in assignments:
            ambiguous_AsPb.append(area)
        else:
            for assignment in assignments:
                emission_areas[assignment] = emission_areas.get(assignment, 0) + area

    as_kbeta_found = ("As Kβ" in emission_areas and not pd.isna(emission_areas["As Kβ"]))
    pb_lbeta_found = ("Pb Lβ" in emission_areas and not pd.isna(emission_areas["Pb Lβ"]))
    for amb_area in ambiguous_AsPb:
        if as_kbeta_found and not pb_lbeta_found:
            emission_areas["As Kα"] = emission_areas.get("As Kα", 0) + amb_area
        elif pb_lbeta_found and not as_kbeta_found:
            emission_areas["Pb Lα"] = emission_areas.get("Pb Lα", 0) + amb_area
        elif as_kbeta_found and pb_lbeta_found:
            emission_areas["As Kα"] = emission_areas.get("As Kα", 0) + amb_area
            emission_areas["Pb Lα"] = emission_areas.get("Pb Lα", 0) + amb_area
        else:
            emission_areas["As Kα"] = emission_areas.get("As Kα", 0) + amb_area
            emission_areas["Pb Lα"] = emission_areas.get("Pb Lα", 0) + amb_area

    expected_emissions = {
        'As': ['As Kα', 'As Kβ'],
        'Pb': ['Pb Lα', 'Pb Lβ'],
        'Cu': ['Cu Kα', 'Cu Kβ'],
        'Hg': ['Hg Lα', 'Hg Lβ'],
        'S':  ['S Kα']}

    for element in ['As', 'Cu', 'Pb', 'Hg']:
        keys = expected_emissions[element]
        if not all(key in emission_areas for key in keys):
            for key in keys:
                emission_areas[key] = np.nan

    if 'As Kα' in emission_areas and 'As Kβ' in emission_areas:
        if (not pd.isna(emission_areas['As Kα'])) and (not pd.isna(emission_areas['As Kβ'])):
            if emission_areas['As Kβ'] > emission_areas['As Kα']:
                emission_areas['As Kα'] = np.nan
                emission_areas['As Kβ'] = np.nan

    if 'S Kα' not in emission_areas:
        emission_areas['S Kα'] = np.nan

    emission_areas['Well'] = sample_name

    if plot:
        plt.figure(figsize=(10, 6))
        plt.plot(energy, intensity, label="Emission Spectrum", color='black')
        plt.plot(energy[peaks], intensity[peaks], "rx", markersize=8, label="Detected Peaks")

        filled_once = False
        for ann in peak_annotations:
            if not filled_once:
                plt.fill_between(energy[ann['left']:ann['right'] + 1],
                                 intensity[ann['left']:ann['right'] + 1],
                                 color='lightblue', alpha=0.4, label="Integrated Area")
                filled_once = True
            else:
                plt.fill_between(energy[ann['left']:ann['right'] + 1],
                                 intensity[ann['left']:ann['right'] + 1],
                                 color='lightblue', alpha=0.4)
            text = (f"{ann['energy']:.2f} keV\nArea: {ann['area']:.1f}\n" +
                    (", ".join(ann['assignments']) if ann['assignments'] else "Unassigned"))
            plt.annotate(text,
                         (ann['energy'], ann['intensity']),
                         textcoords="offset points",
                         xytext=(0, 10),
                         ha="center",
                         fontsize=8,
                         color='blue')

        plt.xlabel("Energy (keV)")
        plt.ylabel("Intensity (counts)")
        plt.title(f"µXRF Spectrum - {sample_name}")
        plt.legend()
        plt.tight_layout()
        plt.show()

    return emission_areas

def process_samples(sample_dict, distance=5, tolerance=0.2, background_sample=None):
    """
       Process multiple µXRF samples.

       Parameters:
         sample_dict: dictionary where keys are sample names and values are DataFrames
                      with 'Energie' and 'Impulse' columns.

       Returns:
         A DataFrame with each sample as a row and columns for the sample name and integrated peak areas.
       """
    if background_sample == '':
        background_sample = None
    results = []
    for sample_name, df in sample_dict.items():
        results.append(process_sample(sample_name=sample_name, df=df, distance=distance, tolerance=tolerance, background_sample=background_sample, sample_dict=sample_dict))
    result_df = pd.DataFrame(results)

    cols = result_df.columns.tolist()
    if 'sample' in cols:
        cols.insert(0, cols.pop(cols.index('sample')))
    result_df = result_df[cols]
    return result_df
