import tkinter as tk
from tkinter import ttk
import ColorMaps

class DisplayOptions:
    def __init__(self, master_window):
        self.master_window = master_window

        self.window = tk.Toplevel(self.master_window)
        self.window.withdraw()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.colormap_label = tk.Label(master=self.window,
                                       text='Colormap')
        self.colormap_label.grid(row=0, column=0)

        colormaps = ['Yellow', 'Blue', 'Red', 'Cyan', 'Green', 'Dark Green', 'Orange']
        self.colormap = tk.StringVar()
        self.colormap_combobox = ttk.Combobox(master=self.window, values=colormaps)
        self.colormap_combobox.set('Green')
        self.colormap_combobox.grid(row=1, column=0, padx=10)

        self.min_value_label = tk.Label(master=self.window,
                                        text='Min Value')
        self.min_value_label.grid(row=2, column=0)

        self.min_value = tk.StringVar(value='None')
        self.min_value_entry = tk.Entry(master=self.window, textvariable=self.min_value)
        self.min_value_entry.grid(row=3, column=0)

        self.max_value_label = tk.Label(master=self.window,
                                        text='Max Value')
        self.max_value_label.grid(row=4, column=0)

        self.max_value = tk.StringVar(value='None')
        self.max_value_entry = tk.Entry(master=self.window, textvariable=self.max_value)
        self.max_value_entry.grid(row=5, column=0, pady=(0,10))

    def open_window(self):
        self.window.deiconify()

    def reset_options(self):
        self.min_value.set('None')
        self.max_value.set('None')
        self.colormap_combobox.set('Green')

    def on_close(self):
        self.window.withdraw()
