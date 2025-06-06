from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import GUI_Master

import tkinter as tk
from tkinter import ttk

def drop_logfile(event):
    GUI_Master.GUI.logfile_filepath = event.data
    GUI_Master.GUI.import_logfile(dropped=True)


class CustomTreeview(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure the custom header style
        style = ttk.Style(self)
        style.configure("Custom.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Apply the custom style to the Treeview widget
        self["style"] = "Custom.Treeview"


class GUIWidgets:
    def __init__(self, gui_master: GUI_Master.GUI, master_window):
        self.gui_master = gui_master
        self.master_window = master_window

        # Creating GUI-Widgets displayed in the main window
        self.treeview_frame = ttk.Frame(master=self.master_window,
                                         width=540,
                                         height=370)
        self.import_logfile_button = ttk.Button(master=self.treeview_frame,
                                                text='Import Logfile',
                                                command=self.gui_master.import_logfile,
                                                width=40)
        self.logfile_treeview = CustomTreeview(master=self.treeview_frame,
                                               height=15, show='headings',
                                               columns='Logfile')
        self.logfile_treeview.heading(column='# 1',
                                      text='Logfile')

        self.import_samples_button = ttk.Button(master=self.treeview_frame,
                                                text='Import Sample',
                                                command=self.gui_master.import_samples,
                                                width=40)
        self.samples_treeview = CustomTreeview(master=self.treeview_frame,
                                               height=15,
                                               show='headings',
                                               columns='Samples')
        self.samples_treeview.column(column="# 1",
                                     anchor=tk.CENTER,
                                     stretch=tk.NO, width=250)
        self.samples_treeview.heading(column='# 1',
                                      text='Samples')
        # The bottom line menu
        self.conversion_frame = ttk.Frame(master=self.master_window,
                                          width=820,
                                          height=100)
        self.export_path = tk.StringVar()
        self.directory_entry = ttk.Entry(master=self.conversion_frame,
                                         state='readonly',
                                         textvariable=self.export_path,
                                         width=50)
        self.browse_directory_button = ttk.Button(master=self.conversion_frame,
                                                  text='Browse',

                                                  command=self.gui_master.export_directory)

        self.lbl_file = ttk.Label(master=self.conversion_frame, text="")
        self.btn_browse = ttk.Button(master=self.conversion_frame,
                                    text="Import Well Data",
                                    command=self.gui_master.importer.import_well_data)



        self.data_chosen = tk.StringVar()
        self.choose_data_combobox = ttk.Combobox(master=self.conversion_frame)
        self.go_button = ttk.Button(master=self.conversion_frame,
                                    text='Load Data',
                                    command=self.gui_master.build_experiment_objects)
        self.build_laser_duration_button = ttk.Button(master=self.conversion_frame,
                                                      text='Export Data',
                                                      command=self.gui_master.export_data)
        self.progress = tk.IntVar()
        self.progressbar = ttk.Progressbar(master=self.conversion_frame,
                                           mode='determinate',
                                           maximum=100,
                                           orient=tk.HORIZONTAL,
                                           length=810,
                                           variable=self.progress)

        # The Move Sample Menu
        self.move_frame = ttk.Frame(master=self.master_window,
                                         width=300,
                                         height=80)
        self.background_sample_state = tk.IntVar()
        self.background_sample_state.set(0)
        self.background_sample_checkbutton = ttk.Checkbutton(master=self.move_frame,
                                         text="Use Sample as Background",
                                                             onvalue=1,
                                                             offvalue=0,
                                                             variable=self.background_sample_state,
                                         command=self.gui_master.enable_background_sample_entry,
                                         width=28)
        self.background_sample = tk.StringVar()
        self.background_sample_entry = ttk.Entry(master=self.move_frame,
                                                  textvariable=self.background_sample,
                                                  width=15,
                                                  state='disabled')
        # The separator menu
        self.separator_frame = ttk.Frame(master=self.master_window,
                                         width=110,
                                         height=120,
                                         relief='groove')
        self.separator_header_import = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter import')
        self.separator_import = tk.StringVar(value=';')
        option_list = ('Semicolon', 'Comma', 'Tab', 'Space')
        self.separator_menu_import = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_import,
                                                    *option_list)
        self.separator_header_export = ttk.Label(master=self.separator_frame,
                                                 text='Delimiter export')
        self.separator_export = tk.StringVar(value='Semicolon')
        self.separator_menu_export = ttk.OptionMenu(self.separator_frame,
                                                    self.separator_export,
                                                    *option_list)

        # The data type menu
        self.datatype_frame = ttk.Frame(master=self.master_window,
                                        width=240,
                                        height=100,
                                        relief='groove')
        self.header_instruments = ttk.Label(master=self.datatype_frame,
                                            text='Data Type',
                                            borderwidth=5)
        self.data_type = tk.StringVar()
        self.data_type.set('iCap TQ')
        self.icap_tq_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                   text='iCap TQ',
                                                   variable=self.data_type,
                                                   value='iCap TQ',
                                                   command=self.gui_master.change_of_instrument)
        self.uxrf_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='µXRF',
                                                       variable=self.data_type,
                                                       value='µXRF',
                                                       command=self.gui_master.change_of_instrument)

        self.master_window.grid_columnconfigure(index=0, weight=1)
        self.master_window.grid_columnconfigure(index=1, weight=1)
        self.master_window.grid_columnconfigure(index=2, weight=1)

        # The laser type menu
        self.header_laser = ttk.Label(master=self.datatype_frame,
                                                text='Laser Type',
                                                borderwidth=5)
        self.laser_type = tk.StringVar()
        self.laser_type.set('ImageBIO 266')
        self.imagebio_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                   text='ImageBIO 266',
                                                   variable=self.laser_type,
                                                   value='ImageBIO 266')
        self.cetac_g2plus_radiobutton = ttk.Radiobutton(master=self.datatype_frame,
                                                       text='Cetac G2+',
                                                       variable=self.laser_type,
                                                       value='Cetac G2+')

        #The Synchronization menu
        self.full_synchronization_frame = ttk.Frame(master=self.master_window,
                                               width=820,
                                               height=120)
        self.synchronization_frame = ttk.Frame(master=self.full_synchronization_frame,
                                               width=240,
                                               height=110,
                                               relief='groove')
        self.header_synchronization = ttk.Label(master=self.synchronization_frame,
                                                text='Data Synchronization',
                                                borderwidth=5)
        self.synchronization = tk.BooleanVar(value=False)
        self.checkbutton_synchronization = ttk.Checkbutton(master=self.synchronization_frame,
                                                           text='Synchronization',
                                                           onvalue=True,
                                                           offvalue=False,
                                                           variable=self.synchronization,
                                                           command=self.gui_master.change_of_synchronization_mode)
        self.button_synchronization = ttk.Button(master=self.synchronization_frame,
                                                 text='Synchronize',
                                                 command=self.gui_master.synchronize_data,
                                                 state='disabled')

        self.data_status_frame = ttk.Frame(master=self.full_synchronization_frame,
                                          width=525,
                                          height=100)
        self.logfile_status_frame = ttk.Frame(master=self.data_status_frame,
                                           width=253,
                                           height=100,
                                           relief='groove')
        self.multiple_samples_detected = tk.BooleanVar(value=False)
        self.multiple_samples_detected_checkbutton = ttk.Checkbutton(master=self.logfile_status_frame,
                                                                     text='Multiple Samples Found',
                                                                     variable=self.multiple_samples_detected,
                                                                     state='disabled',
                                                                     onvalue=True,
                                                                     offvalue=False)
        self.sample_status_frame = ttk.Frame(master=self.data_status_frame,
                                              width=254,
                                              height=100,
                                              relief='groove')
        self.data_is_synchronized = tk.BooleanVar(value=False)
        self.data_is_synchronized_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                text='Data is Synchronized',
                                                                variable=self.data_is_synchronized,
                                                                state='disabled',
                                                                onvalue=True,
                                                                offvalue=False)
        self.first_line_for_synchronization = tk.BooleanVar(value=False)
        self.first_line_for_synchronization_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                          text='First Line Used for Synchronization',
                                                                          variable=self.first_line_for_synchronization,
                                                                          state='disabled',
                                                                          onvalue=True,
                                                                          offvalue=False)
        self.background_corrected = tk.BooleanVar(value=False)
        self.background_corrected_checkbutton = ttk.Checkbutton(master=self.sample_status_frame,
                                                                text='Data is Background Corrected',
                                                                variable=self.background_corrected,
                                                                state='disabled',
                                                                onvalue=True,
                                                                offvalue=False)

    def grid_gui_widgets(self):
        """
        Grids all Tk GUI widgets that have been defined during the innitiation of the PostAblationGUI Class
        :return: None
        """

        self.treeview_frame.grid(row=0, column=0, columnspan=1, rowspan=5, sticky='w', padx=(24, 0))
        self.treeview_frame.grid_propagate(False)
        self.import_logfile_button.grid(row=0, column=0, pady=5, padx=10)
        self.logfile_treeview.column("# 1", anchor=tk.CENTER, stretch=tk.NO, width=250)
        self.logfile_treeview.grid(row=1, column=0, rowspan=2, pady=5)
        self.import_samples_button.grid(row=0, column=1, pady=5, padx=10)
        self.samples_treeview.grid(row=1, column=1, rowspan=2, pady=5)

        self.move_frame.grid(row=0, column=1, columnspan=2, sticky='nw')
        self.background_sample_checkbutton.grid(row=0, column=0, columnspan=2, pady=(5, 0), padx=5)
        self.background_sample_entry.grid(row=1, column=0, pady=10, padx=5)

        self.datatype_frame.grid(row=4, column=1, pady=(10,0), rowspan=2, sticky='w')
        self.datatype_frame.grid_propagate(False)
        self.header_instruments.grid(row=0, column=0, pady=(5, 0))
        self.icap_tq_radiobutton.grid(row=1, column=0, padx=(5,0))
        self.uxrf_radiobutton.grid(row=2, column=0, sticky='w', padx=(5,0))
        self.header_laser.grid(row=0, column=1, pady=(10, 0))
        self.imagebio_radiobutton.grid(row=1, column=1, padx=(10,0))
        self.cetac_g2plus_radiobutton.grid(row=2, column=1, sticky='w', padx=(10,0))

        self.full_synchronization_frame.grid(row=6, column=0, pady=(10,0), columnspan=2, sticky='w', padx=(24, 0))
        self.full_synchronization_frame.grid_propagate(False)

        self.synchronization_frame.grid(row=0, column=1, pady=(5, 0), padx=(36, 0))
        self.synchronization_frame.grid_propagate(False)
        self.header_synchronization.grid(row=0, column=0, sticky='ne', pady=(5, 0), padx=10, columnspan=2)
        self.checkbutton_synchronization.grid(row=1, column=0, sticky='w', padx=(5,0), pady=(5,0))
        self.button_synchronization.grid(row=2, column=0, pady=(5,0))

        self.data_status_frame.grid(row=0, column=0, pady=5, padx=9)
        self.data_status_frame.grid_propagate(False)
        self.logfile_status_frame.grid(row=0, column=0)
        self.logfile_status_frame.grid_propagate(False)
        self.sample_status_frame.grid(row=0, column=1, padx=(16, 0))
        self.sample_status_frame.grid_propagate(False)

        self.conversion_frame.grid(row=7, column=0, pady=10, columnspan=2, sticky='w', padx=(24,0))
        self.conversion_frame.grid_propagate(False)
        self.directory_entry.grid(row=0, column=0, pady=(5, 0), columnspan=2, padx=(10, 0))
        self.browse_directory_button.grid(row=0, column=3, pady=(5, 0), sticky='w')

        self.lbl_file.grid(row=1, column=0, pady=(5, 0), columnspan=2, padx=(10, 0))
        self.btn_browse.grid(row=1, column=3, pady=(5, 0), sticky='w')

        self.choose_data_combobox.grid(row=0, column=4, pady=(5, 0), sticky='w')
        self.go_button.grid(row=0, column=17, pady=(5, 0), sticky='w')
        self.build_laser_duration_button.grid(row=0, column=19, pady=(5,0), sticky='e')
        self.progressbar.grid(row=2, column=0, columnspan=20, pady=(10, 0), padx=(10, 0))
