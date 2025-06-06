import tkinter as tk
from tkinter import filedialog
import os
import ExperimentClass
import GUI_Widgets
import Synchronization
import Importer
import Windows_Notifications


class GUI:
    def __init__(self, master_window, main):
        self.master_window = master_window
        self.main=main
        self.master_window.title("LassoTool")
        self.master_window.geometry('900x620')
        self.master_window.resizable(width=False, height=False)

        self.importer = Importer.Importer(gui=self)
        self.notifications = Windows_Notifications.Notifications(gui=self)

        self.widgets = GUI_Widgets.GUIWidgets(gui_master=self,
                                              master_window=master_window)
        self.experiment = None

        self.list_of_files = []
        self.filename_list = []
        self.idxs = None
        self.pattern_csv_filepath_without_filename = None
        self.export_path_list = None
        self.logfile_filename = None
        self.logfile_filepath = None

        self.synchronizer = Synchronization.ImageSynchronizer(master_gui=self, master_window=self.master_window)
        self.data_is_synchronized = False
        self.data_is_background_corrected = False
        self.data_is_first_line_synchronized = False
        self.well_data = None
    def grid_gui_widgets(self):
        self.widgets.grid_gui_widgets()

    def import_logfile(self, dropped=False):
        """
        Opens the fileselection to select the one logfile of the current experiment. The selected logfile is inserted into
        the corresponding Treeview. Only one logfile can be imported for
        one Experiment
        :return: The directory which was chosen by the user to contain the logfile
        """
        if dropped is False:
            self.logfile_filepath: str = tk.filedialog.askopenfilename(title='Choose a logfile',
                                                                   filetypes=[('CSV', '*.csv')])

        self.logfile_filename: list = [os.path.basename(self.logfile_filepath)]
        for item in self.widgets.logfile_treeview.get_children():
            self.widgets.logfile_treeview.delete(item)
        self.widgets.logfile_treeview.insert(parent='',
                                             index=0,
                                             text='',
                                             values=self.logfile_filename)
        self.reset_progress()
        self.update_status(reset=True)
        return self.logfile_filepath

    def import_samples(self):
        """
        Opens the fileselection to select one or more sample folders/files of the current experiment. The selected
        folders/files is inserted into the corresponding Treeview. Resets the list of files and filenames and
        updates them with the new samples.
        """
        if self.widgets.data_type.get() == 'iCap TQ':
            self.list_of_files = []
            self.filename_list = []

            samples_filepath = tk.filedialog.askopenfilenames(title='Choose your sample files',
                                                              filetypes=[('CSV', '*.csv')])

            for i in samples_filepath:
                filename = os.path.basename(i)
                if filename in self.filename_list:
                    continue
                else:
                    self.filename_list.append(filename)

            for i in samples_filepath:
                if i in self.list_of_files:
                    continue
                else:
                    self.list_of_files.append(i)

        if self.widgets.data_type.get() == 'µXRF':
            self.list_of_files = []
            self.filename_list = []
            folder_filepath = tk.filedialog.askdirectory(title='Choose your sample folder')


            self.list_of_files.append(folder_filepath)
            foldername = os.path.basename(folder_filepath)
            self.filename_list.append(foldername)


        for item in self.widgets.samples_treeview.get_children():
            self.widgets.samples_treeview.delete(item)

        for i, k in enumerate(self.filename_list):
            self.widgets.samples_treeview.insert(parent='', index=i, text='', values=[str(k)])

        self.reset_progress()
        self.update_status(reset=True)

    def change_of_instrument(self):
        """
        When the user switches the data type of the mass spec, both treeviews are reset to show the
        user that there is no compatibility between these data types. The import separator is adjusted to reflect
        the most likely separator type of th current data type.
        """
        if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')
            self.widgets.checkbutton_synchronization.configure(state=tk.ACTIVE)
        if self.widgets.data_type.get() == 'µXRF':
            self.widgets.import_samples_button.configure(text='Import Sample')
            self.widgets.separator_import.set(';')
            self.widgets.import_logfile_button.configure(state=tk.DISABLED)
            for item in self.widgets.logfile_treeview.get_children():
                self.widgets.logfile_treeview.delete(item)
            self.logfile_filename = []
            self.widgets.checkbutton_synchronization.configure(state=tk.DISABLED)

    def change_of_synchronization_mode(self):
        if self.widgets.synchronization.get():
            self.widgets.button_synchronization.configure(state='active')
            if self.widgets.data_type.get() == 'iCap TQ (Daisy)':
                self.widgets.separator_import.set(',')
        else:
            self.widgets.button_synchronization.configure(state='disabled')

        self.update_status()

    def enable_background_sample_entry(self):
        if self.widgets.background_sample_state.get() == 1:
            self.widgets.background_sample_entry.configure(state='active')
        else:
            self.widgets.background_sample_entry.configure(state='disabled')

    def build_experiment_objects(self):
        """
        Collect the data from the logfile and samples files/folders and creates the managing experiment instance
        for the whole conversion.
        """
        self.reset_progress()

        synchronized = self.synchronization_query()

        sample_rawdata_dictionary = self.importer.import_sample_file(data_type=self.widgets.data_type.get(),
                                                                     synchronized=synchronized)

        if self.widgets.data_type.get() != 'µXRF':

            logfile_dataframe = self.importer.import_laser_logfile(logfile=self.logfile_filepath,
                                                                   laser_type=self.widgets.laser_type.get(),
                                                                   iolite_file=synchronized,
                                                                   rectangular_data_calculation=True)
        else:
            logfile_dataframe = None

        self.experiment = ExperimentClass.Experiment(gui=self,
                                                     raw_laser_logfile_dataframe=logfile_dataframe,
                                                     sample_rawdata_dictionary=sample_rawdata_dictionary,
                                                     data_type=self.widgets.data_type.get(),
                                                     logfile_filepath=self.logfile_filepath,
                                                     synchronized=synchronized)

        self.experiment.build_rectangular_data()

    def update_status(self, reset=False):
        if reset:
            self.data_is_synchronized = False
            self.data_is_background_corrected = False
            self.data_is_first_line_synchronized = False
            self.widgets.data_is_synchronized_checkbutton.grid_remove()
            self.widgets.background_corrected_checkbutton.grid_remove()
        if self.widgets.synchronization.get():
            self.widgets.data_is_synchronized_checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky='w')
            self.widgets.data_is_synchronized.set(self.data_is_synchronized)
            self.widgets.background_corrected_checkbutton.grid(row=2, column=0, padx=5, pady=5, sticky='w')
            self.widgets.background_corrected.set(self.data_is_background_corrected)
        if self.widgets.synchronization.get() is False:
            self.widgets.data_is_synchronized_checkbutton.grid_remove()
            self.widgets.background_corrected_checkbutton.grid_remove()

    def create_new_window(self, name):
        self.new_Window = tk.Toplevel(self.master_window)
        self.new_Window.title(name)

        return self.new_Window
    def synchronization_query(self):
        if self.data_is_synchronized and self.widgets.synchronization:
            synchronized = True
        elif self.data_is_synchronized and self.widgets.synchronization.get() is False:
            decider = self.notifications.notification_yesno(header='Synchronization Warning',
                                               body='Your data is successfully synchronised but you have not ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the synchronized data?')
            synchronized = decider
        elif self.data_is_synchronized is False and self.widgets.synchronization.get():
            decider = self.notifications.notification_yesno(header='Synchronization Warning',
                                               body='Your data not synchronised but you have ticked '
                                                       'the Synchronize Checkbox. Do you want to continue '
                                                       'with the unsynchronized data?')
            synchronized = decider
        else:
            synchronized = False
        return synchronized

    def synchronize_data(self):
        state = self.synchronizer.synchronize_data(data_type=self.widgets.data_type.get(),
                                           import_separator=self.widgets.separator_import.get(),
                                           laser=self.widgets.laser_type.get())
        if state is False:
            return
        self.synchronizer.toggle_window_visivility()

    def export_data(self):
        self.experiment.export_data(sample=self.filename_list[0], export_directory=self.get_export_path())

    def open_options_menu(self):
        self.options_menu.open_window()

    def export_directory(self):
        """
        Update the path selected by the user and shown in the path entry field.
        """
        path = filedialog.askdirectory()
        self.widgets.export_path.set(path)
        self.widgets.directory_entry.delete(0, tk.END)
        self.widgets.directory_entry.insert(0, path)

    def get_separator_export(self):
        """
        Give the separator for the exported files chosen by the user to a requesting instance.
        """
        separator_list = self.widgets.separator_export.get()
        if separator_list == 'Tab':
            separator = '\t'
        elif separator_list == 'Space':
            separator = ' '
        elif separator_list == 'Comma':
            separator = ','
        elif separator_list == 'Semicolon':
            separator = ';'
        return separator

    def get_separator_import(self):
        """
        Give the separator for the exported files chosen by the user to a requesting instance.
        """
        separator_list = self.widgets.separator_import.get()
        if separator_list == 'Tab':
            separator = '\t'
        elif separator_list == 'Space':
            separator = ' '
        else:
            separator = separator_list
        return separator

    def get_export_path(self):
        """
        Give the export path chosen by the user to a requesting instance.
        """
        return self.widgets.export_path.get()

    def increase_progress(self, step):
        """
        Update the progress bar to increase the progress shown by a supplied step size
        """
        current_progress = self.widgets.progress.get()
        self.widgets.progress.set(current_progress + step)
        self.master_window.update_idletasks()

    def reset_progress(self):
        """
        Reset the progress bar to show no progress.
        """
        self.widgets.progress.set(0)
        self.master_window.update_idletasks()
