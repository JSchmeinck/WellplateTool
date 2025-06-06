# WellplateTool
WellplateTool is a used to process and evaluate data from well plate analyses by means of LA-ICP-MS and µXRF in an automated way. The specific use case is the analysis of arsenic containing pigments in historic book bindings. Samples are assigned to one of four pigment groups based on the differences in their signal intensity or area of Cu and As. The output is an excel file.

## How to use
### LA-ICP-MS
After selecting the correct LA system, the user has to import a logfile from the LA system and the raw data from the MS, both as CSV files. The MS data is expected to be in the form of one continuous analysis for the whole well plate. 
The formatting of the MS CSV data is based on the export of the Thermo iCap TQ using Qtegra. 
The data first has to be snychronized by checking the "Synchronization" checkmark and then clicking the "Synchronize" button. 
A new window will open, showing a graph. In blue, the TIC of the MS raw data is shown. 
In green, the on/off signal of the laser is showns. 
The laser data has to be shifted to be synchronized with the MS data if both instruments were not started simultaneously. 
This can be done by via buttons below the graph or by holding shift and holding the left mouse button while in the graph window. 
After synchronizing the data and hitting accept, an export path and a well data path have to be added at the bottom of the main window. 
The well data file is a CSV file that has to include well positions (in the form of a letter and a number e.g. "A3") and the sample name as separate columns. 
Finally, the "Load Data" and then the "Export Data" buttons can be clicked to export the exel file to the specified path.

### µXRF
The user first has to select "µXRF" as the data type and then import raw data from the µXRF system. The µXRF data import is based on the Bruker M4 Tornado. 
Data is expected to be in the form of 9 spectra CSV files for each position on the well plate.
The data is ordered as subfolders for each positon on the well plate (For example the data for the position A3 will be found in the "A" folder in the "3" folder) 
An export path and a well data path have to be added at the bottom of the main window. 
The well data file is a CSV file that has to include well positions (in the form of a letter and a number e.g. "A3") and the sample name as separate columns. 
Finally, the "Load Data" button is clicked. After the processing of te data is completed, the "Export Data" can be clicked to export the exel file to the specified path.
