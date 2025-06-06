import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import numpy as np
from datetime import datetime
import keyboard
from tkinter import ttk
from tkinter import Menu


def mask_array(main_array, mask_array, on_value, timestamp_array):

    mask = np.ma.masked_invalid(mask_array, copy=True)

    boolean_mask = np.ma.getmaskarray(mask)

    inverted_boolean_mask = np.invert(boolean_mask)
    masked_array = np.where(boolean_mask, 0, main_array)

    masked_array[inverted_boolean_mask] = on_value

    reduced_on_array = masked_array[masked_array != 0]

    zeros_array = np.array([0, 0])

    extended_array = []
    for i, value in enumerate(reduced_on_array):
        extended_array.append(value)
        if i % 2 == 1:
            extended_array.extend(zeros_array)

    extended_array = np.insert(extended_array, 0, 0)

    extended_array = np.delete(extended_array, -1)


    time_objects = [datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f') for time_str in timestamp_array]

    start_time = time_objects[0]
    time_diffs = [(time - start_time).total_seconds() for time in time_objects]

    time_diff_array = np.array(time_diffs)

    masked_array_time = np.where(boolean_mask, -1, time_diff_array)

    reduced_time_array = masked_array_time[masked_array_time != -1]

    duplicated_time_array = reduced_time_array.repeat(2)

    return extended_array, inverted_boolean_mask, duplicated_time_array, reduced_time_array




class ImageSynchronizer:
    def __init__(self, master_gui, master_window):
        self.gui = master_gui
        self.master = master_window
        self.window = tk.Toplevel(master=master_window)
        self.window.title("Image Synchronization")
        self.window.geometry('750x650')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.resizable(width=False, height=False)
        self.window.withdraw()

        self.fig = plt.figure(frameon=False)
        self.ax = self.fig.add_axes([0.08, 0.09, 0.9, 0.85])

        self.image_data = None
        self.image_time = None
        self.image_intensity = None
        self.laser_logfile = None
        self.laser_log_time = None
        self.shifted_laser_log_time = None
        self.clean_time_array = None
        self.clean_time_array_extended = None
        self.time_data_sample = None

        self.laser_log_status = None
        self.filename = None
        self.directory = None

        self.laser_start_times_pointers = []
        self.laser_stop_times_pointers = []

        self.plot_frame = ttk.Frame(master=self.window, width=700, height=500)
        self.plot_frame.grid_propagate(False)
        self.plot_frame.grid(row=0, column=0, padx=50, pady=20, sticky='nesw')

        self.peripheral_frame = ttk.Frame(master=self.window, width=1000, height=100)
        self.peripheral_frame.grid(row=1, column=0, padx=50)

        self.click_offset = 0
        self.offset_axis = 0
        self.laser_log_time_offset = 0
        self.laser_log_time_extension = 0
        self.logfile_mask = None
        self.samples = None
        self.sample_rawdata = None
        self.synchronized_data = None
        self.indices_dictionary = {}
        self.list_of_unique_masses_in_file = None
        self.data_type = None
        self.import_separator = None

        self.move_left_button = ttk.Button(master=self.peripheral_frame,
                                           text='Move Left',
                                           command=lambda: self.move_laser_log_time(direction='left'))
        self.move_left_button.grid(row=0, column=0, sticky='e')
        self.move_increment = tk.DoubleVar(value=1.0)
        self.move_increment_entry = ttk.Entry(master=self.peripheral_frame,
                                              textvariable=self.move_increment,
                                              width=10)
        self.move_increment_entry.grid(row=0, column=1)
        self.move_right_button = ttk.Button(master=self.peripheral_frame,
                                            text='Move Right',
                                            command=lambda: self.move_laser_log_time(direction='right'))
        self.move_right_button.grid(row=0, column=2, sticky='w')
        self.reset_button = ttk.Button(master=self.peripheral_frame,
                                       text='Reset Offset',
                                       command=self.reset_offset,
                                       width=17)
        self.reset_button.grid(row=0, column=3)
        self.current_offset_label = ttk.Label(master=self.peripheral_frame,
                                              text='Current Offset:')
        self.current_offset_label.grid(row=0, column=4, sticky='e')
        self.current_offset = tk.StringVar(value='0 s')
        self.current_offset_entry = ttk.Label(master=self.peripheral_frame,
                                              textvariable=self.current_offset,
                                              state=tk.DISABLED)
        self.current_offset_entry.grid(row=0, column=5, padx=20)

        self.accept_button = ttk.Button(master=self.peripheral_frame,
                                        text='Accept', command=self.accept)
        self.accept_button.grid(row=0, column=7)

        self.background_correction = tk.BooleanVar(value=False)
        self.background_correction_checkbutton = ttk.Checkbutton(master=self.peripheral_frame,
                                                                 text='Background Correction',
                                                                 onvalue=True,
                                                                 offvalue=False,
                                                                 variable=self.background_correction,
                                                                 command=self.show_background_correction)
        self.background_correction_checkbutton.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        self.background_correction_offset_label = ttk.Label(master=self.peripheral_frame,
                                                            text='Offset')
        self.background_correction_offset_label.grid(row=2, column=2, columnspan=2, pady=(10, 0), sticky='e')
        self.background_correction_offset = tk.DoubleVar(value=0.0)
        self.background_correction_offset_entry = ttk.Entry(master=self.peripheral_frame,
                                                            textvariable=self.background_correction_offset,
                                                            state='disabled',
                                                            width=10)
        self.background_correction_offset_entry.bind("<Return>", self.update_background_correction)
        self.background_correction_offset_entry.grid(row=2, column=4, pady=(10, 0), sticky='w')

        self.background_correction_length_label = ttk.Label(master=self.peripheral_frame,
                                                            text='Window Length')
        self.background_correction_length_label.grid(row=2, column=5, pady=(10, 0))
        self.background_correction_length = tk.DoubleVar(value=5.0)
        self.background_correction_length_entry = ttk.Entry(master=self.peripheral_frame,
                                                            textvariable=self.background_correction_length,
                                                            state='disabled',
                                                            width=10)
        self.background_correction_length_entry.bind("<Return>", self.update_background_correction)
        self.background_correction_length_entry.grid(row=2, column=6, pady=(10, 0))


        self.laser_log_plot = None
        self.raw_data_plot = None
        self.canvas = None
        self.dragging_line = False
        self.dragging_xaxis = False

        self.multi_import = False

        self.tic_data = None
        self.masses = None

        self.sample_data_dictionary = {}

        self.background_lines_dictionary = {}

    def on_closing(self):
        self.window.withdraw()

    def set_laser_logfile(self, logfile):
        self.laser_logfile = logfile

    def set_image_data(self, image_data):
        self.image_data = image_data

    def plot_laser_log_and_image_data(self, time, intensity):
        self.clean_time_array_extended = self.clean_time_array.copy()

        if self.multi_import is False:
            self.laser_log_plot = self.ax.plot(self.laser_log_time, self.laser_log_status, 'g', picker=5)
            self.raw_data_plot = self.ax.plot(time, intensity, 'b-', picker=5)
            self.ax.set_xlabel('Time / s')
            self.ax.set_ylabel('Intensity')
            self.ax.ticklabel_format(style='sci', scilimits=(0, 0))
            self.ax.set_title('Synchronization')

            self.fig.canvas.mpl_connect('axes_enter_event', self.on_axes_enter)
            self.fig.canvas.mpl_connect('axes_leave_event', self.on_axes_leave)
            self.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
            self.fig.canvas.mpl_connect('button_release_event', self.on_button_release)
            self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.fig.canvas.mpl_connect('button_release_event', self.on_release)
            self.fig.canvas.mpl_connect('scroll_event', self.zoom)

        else:
            self.laser_log_plot[0].set_data(self.laser_log_time, self.laser_log_status)
            self.raw_data_plot[0].set_data(time, intensity)
            self.ax.relim()
            self.ax.autoscale()

        if self.multi_import is False:
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
            self.canvas.get_tk_widget().bind("<Button-3>", self.on_right_click)
            self.multi_import = True
        else:
            self.canvas.draw()

    def change_image_data(self, mass):
        if mass == 'TIC':
            self.raw_data_plot[0].set_ydata(self.tic_data)
            maximum = np.max(self.tic_data) * 1.2
            y_data = self.laser_log_plot[0].get_ydata()
            y_data[y_data > 0] = maximum
            self.laser_log_plot[0].set_ydata(y_data)
        else:
            self.raw_data_plot[0].set_ydata(self.sample_rawdata[mass].values.astype(float))
            maximum = float(np.max(self.sample_rawdata[mass].values.astype(float))) * 1.2
            y_data = self.laser_log_plot[0].get_ydata()
            y_data[y_data > 0] = maximum
            self.laser_log_plot[0].set_ydata(y_data)
        self.ax.relim()
        self.ax.autoscale()
        self.canvas.draw()

    def on_right_click(self, event):
        context_menu = Menu(self.window, tearoff=0)
        sorted_masses = sorted(self.masses)
        for mass in sorted_masses:
            if mass == 'TIC':
                context_menu.add_command(label=mass,
                                         command=lambda mass=mass: self.change_image_data(mass=mass))
            else:
                context_menu.add_command(label=str(mass), command=lambda mass=mass: self.change_image_data(mass=mass))

        context_menu.post(event.x_root, event.y_root)

    def show_background_correction(self):
        if self.background_correction.get():
            self.background_correction_offset_entry.configure(state='active')
            self.background_correction_length_entry.configure(state='active')

            x_data = self.laser_log_plot[0].get_xdata()[0::4].repeat(2)
            x_data[0::2] = x_data[0::2] - self.background_correction_offset.get() - self.background_correction_length.get()
            x_data[1::2] = x_data[1::2] - self.background_correction_offset.get()

            y_data = np.zeros_like(x_data)

            ticker = 0
            for x_min, x_max, y_value in zip(x_data[::2], x_data[1::2], y_data[::2]):

                line = self.ax.hlines(xmin=x_min, xmax=x_max, y=y_value, colors='r')

                self.background_lines_dictionary[f'{self.samples[ticker]}'] = line
                ticker += 1

            self.fig.canvas.draw()


        else:
            self.background_correction_offset_entry.configure(state='disabled')
            self.background_correction_length_entry.configure(state='disabled')

            for i in self.background_lines_dictionary.values():
                i.remove()
            self.fig.canvas.draw()

    def update_background_correction(self, event):
        if self.background_correction.get():
            for i in self.background_lines_dictionary.values():
                i.remove()

            self.background_lines_dictionary = {}

            x_data = self.laser_log_plot[0].get_xdata()[0::4].repeat(2)
            x_data[0::2] = x_data[0::2] - self.background_correction_offset.get() - self.background_correction_length.get()
            x_data[1::2] = x_data[1::2] - self.background_correction_offset.get()

            y_data = np.zeros_like(x_data)

            ticker = 0
            for x_min, x_max, y_value in zip(x_data[::2], x_data[1::2], y_data[::2]):
                line = self.ax.hlines(xmin=x_min, xmax=x_max, y=y_value, colors='r')

                self.background_lines_dictionary[f'{self.samples[ticker]}'] = line
                ticker += 1

            self.fig.canvas.draw()
        else:
            self.fig.canvas.draw()
    def toggle_window_visivility(self):
        if self.window.winfo_viewable():
            self.window.withdraw()
        else:
            self.window.deiconify()

    def zoom(self, event):

        fig_x, fig_y = self.fig.transFigure.inverted().transform((event.x, event.y))

        ax_left, ax_bottom, ax_width, ax_height = self.ax.get_position().bounds

        margin = 0.05

        if (ax_left - margin <= fig_x <= ax_left + margin):
            cur_ylim = self.ax.get_ylim()
            cur_yrange = (cur_ylim[1] - cur_ylim[0]) * .5
            if event.button == 'up':
                scale_factor = 0.3

                xmax = cur_ylim[1] - cur_yrange * scale_factor

                self.ax.set_ylim([-(0.04353*xmax), cur_ylim[1] - cur_yrange * scale_factor])

                self.update_y_values_of_laser_log_plot(cur_ylim)

            elif event.button == 'down':
                scale_factor = 0.3
                xmax = cur_ylim[1] - cur_yrange * scale_factor

                self.ax.set_ylim([-(0.04353*xmax),
                                  cur_ylim[1] + cur_yrange * scale_factor])

                self.update_y_values_of_laser_log_plot(cur_ylim)

            self.ax.figure.canvas.draw_idle()
            self.window.update()
            return


        else:
            xdata = event.xdata
            ydata = event.ydata

            if xdata is None or ydata is None:
                return

            cur_xlim = self.ax.get_xlim()
            cur_xrange = (cur_xlim[1] - cur_xlim[0]) * .5
            if event.button == 'up':
                scale_factor = 0.3

                self.ax.set_xlim([cur_xlim[0] + cur_xrange * scale_factor, cur_xlim[1] - cur_xrange * scale_factor])

            elif event.button == 'down':
                scale_factor = 0.3
                self.ax.set_xlim([cur_xlim[0] - cur_xrange * scale_factor,
                                      cur_xlim[1] + cur_xrange * scale_factor])
            else:
                return
            self.ax.figure.canvas.draw_idle()
            self.window.update()

    def update_y_values_of_laser_log_plot(self, old_ylim):

        new_ylim = self.ax.get_ylim()

        scale_factor = (new_ylim[1] - new_ylim[0]) / (old_ylim[1] - old_ylim[0])

        new_y = self.laser_log_plot[0].get_ydata() * scale_factor

        self.laser_log_plot[0].set_ydata(new_y)

    def on_button_press(self, event):
        if event.button == 1:
            if event.inaxes is not None and event.inaxes == self.ax:
                self.dragging_xaxis = True
                self.offset_axis = event.xdata
            if event.button == 1:
                self.dragging_line = True
                self.click_offset = event.xdata

    def on_button_release(self, event):
        if event.button == 1:
            self.dragging_line = False
            self.dragging_xaxis = False

    def on_axes_enter(self, event):
        if event.inaxes is not None and event.inaxes == self.ax and self.dragging_xaxis:
            self.dragging_xaxis = True

    def on_axes_leave(self, event):
        self.dragging_xaxis = False

    def on_motion(self, event):

        if self.dragging_line and keyboard.is_pressed("shift"):
            if event.xdata is not None and self.click_offset is not None:
                current_x = event.xdata
                delta_x = current_x - self.click_offset
                self.laser_log_plot[0].set_xdata(self.laser_log_plot[0].get_xdata() + delta_x)
                self.click_offset = current_x

                new_x_data = self.laser_log_plot[0].get_xdata()
                self.laser_log_time_offset = self.laser_log_time[0] - new_x_data[0]
                self.current_offset.set(f'{-round(self.laser_log_time_offset, 2)} s')

        elif self.dragging_xaxis:
            if event.xdata is not None and self.offset_axis is not None:

                cur_xlim = self.ax.get_xlim()
                delta_x = event.xdata - self.offset_axis

                new_x_limits = [cur_xlim[0] - delta_x, cur_xlim[1] - delta_x]
                self.ax.set_xlim(new_x_limits)

        self.update_background_correction(event=None)

    def on_release(self, event):

        self.dragging_line = False
        self.dragging_xaxis = False

    def reset_offset(self):
        self.laser_log_plot[0].set_xdata(self.laser_log_time)
        self.click_offset = 0
        self.current_offset.set(f'{self.click_offset} s')
        self.shifted_laser_log_time = self.laser_log_time
        self.update_background_correction(event=None)

    def move_laser_log_time(self, direction):

        increment = self.move_increment.get()

        old_x = self.laser_log_plot[0].get_xdata()

        if direction == 'left':
            new_x = np.array([x - increment for x in old_x])
            self.laser_log_plot[0].set_xdata(new_x)
            self.click_offset = self.click_offset - increment

        if direction == 'right':
            new_x = np.array([x + increment for x in old_x])
            self.laser_log_plot[0].set_xdata(new_x)
            self.click_offset = self.click_offset + increment

        self.laser_log_time_offset = self.laser_log_time[0] - new_x[0]
        self.current_offset.set(f'{-round(self.laser_log_time_offset, 2)} s')

        self.update_background_correction(event=None)

    def accept(self):
        self.toggle_window_visivility()
        self.current_offset.set(f'0 s')


        self.calculate_samples()

        self.gui.update_status()
        self.gui.build_experiment_objects()

    def get_background_timestamps(self, sample_names_arr):
        background_timestamps = []
        for name in sample_names_arr:
            segments = self.background_lines_dictionary[name].get_segments()
            x_start = segments[0][0]
            x_end = segments[0][1]
            background_timestamps.append(x_start[0])
            background_timestamps.append(x_end[0])
        return np.array(background_timestamps)

    def get_background_corrected_data(self, sample_data, background_data: np.array):
        for column in background_data:
            background_values = background_data[column].values

            background_median = np.median(background_values.astype(float))
            sample_column = sample_data[column].values
            sample_data[column] = sample_column.astype(float)-background_median
        return sample_data
    def calculate_samples(self):
        self.sample_data_dictionary = {}
        self.indices_dictionary = {}

        time_windows_arr = self.clean_time_array_extended - self.laser_log_time_offset
        df = self.sample_rawdata
        sample_names_arr = self.samples

        if self.background_correction.get():
            background_timestamps = self.get_background_timestamps(sample_names_arr=sample_names_arr)

        num_columns = df.shape[1]-1
        list_of_column_names = list(df.columns.values)

        max_length = max(len(time_windows_arr), len(sample_names_arr))

        time_windows_arr = np.pad(time_windows_arr, (0, max_length - len(time_windows_arr)), mode='constant',
                                  constant_values=np.nan)
        sample_names_arr = np.pad(sample_names_arr, (0, max_length - len(sample_names_arr)), mode='constant',
                                  constant_values='')

        samples_data = {}

        column_names_list = []

        for i in range(0, len(time_windows_arr), 2):
            start_time = time_windows_arr[i]
            end_time = time_windows_arr[i + 1]
            sample_name = sample_names_arr[i // 2]

            mask = (df['Time'] >= start_time) & (df['Time'] <= end_time)
            sample_data = df[mask].drop(columns='Time')
            self.indices_dictionary[sample_name] = sample_data.index.tolist()

            if self.background_correction.get():
                background_start_time = background_timestamps[i]
                background_end_time = background_timestamps[i + 1]
                background_mask = (df['Time'] >= background_start_time) & (df['Time'] <= background_end_time)
                background_data = df[background_mask].drop(columns='Time')
                sample_data = self.get_background_corrected_data(sample_data=sample_data,
                                                                 background_data=background_data)

            samples_data[sample_name] = np.concatenate([sample_data[col].values for col in sample_data.columns])

            column_names_list.extend(sample_data.columns)

        decider, length_of_arrays = self.check_array_length(samples_data)

        magic_number = num_columns
        if decider:
            final_step = length_of_arrays / magic_number
        else:
            largest_value = max(length_of_arrays)

            for key, array in samples_data.items():
                if len(array) == largest_value:
                    final_step = len(array) / magic_number
                else:
                    integer = (largest_value - len(array)) / magic_number
                    step = len(array) / magic_number

                    nan_values = np.full((int(integer),), np.nan)
                    for i in range(1, magic_number+1):
                        insert_index = (i * step) + ((i-1) * integer)
                        if insert_index == array.size:
                            array = np.concatenate((array, nan_values))
                        else:
                            array = np.insert(array, int(insert_index), nan_values)

                    samples_data[key] = array

        result_df = pd.DataFrame(samples_data)

        if self.data_type == 'iCap TQ':
            self.list_of_unique_masses_in_file = list_of_column_names[1:]

        for k, i in enumerate(self.list_of_unique_masses_in_file):
            if k == 0:
                mass_name_array = np.full(shape=(int(final_step),), fill_value=i)
            else:
                filler = np.full(shape=(int(final_step),), fill_value=i)
                mass_name_array = np.concatenate((mass_name_array, filler))
        result_df.insert(0, 'Unnamed: 2', mass_name_array)

        self.sample_data_dictionary[self.gui.filename_list[0]] = result_df

        self.gui.data_is_synchronized = True
        if self.background_correction.get():
            self.gui.data_is_background_corrected = True

    def calculate_logfile_extension(self, log_data):
        part_one = [x - self.extension.get() for x in log_data[::2]]
        part_one = np.array(part_one)
        part_two = [x + self.extension.get() for x in log_data[1::2]]
        part_two = np.array(part_two)
        log_x_on_data = np.empty((part_one.size + part_two.size,), dtype=part_one.dtype)
        log_x_on_data[0::2] = part_one
        log_x_on_data[1::2] = part_two
        return log_x_on_data

    def check_array_length(self, data_dict):
        different_num_values = set()

        reference_num_values = data_dict[list(data_dict.keys())[0]].size
        different_num_values.add(reference_num_values)

        for key, arr in data_dict.items():
            current_num_values = arr.size

            if current_num_values != reference_num_values:
                different_num_values.add(current_num_values)

        if different_num_values:
            return False, different_num_values
        else:
            return True, different_num_values

    def synchronize_data(self, data_type, import_separator, laser, test=False, logfile=None):
        if test is False:
            self.directory = self.gui.list_of_files[0]
            self.filename = self.gui.filename_list[0]
            logfile = self.gui.logfile_filepath

        if data_type == 'iCap TQ':
            with open(self.directory) as file:
                rawdata_dataframe = pd.read_csv(file, skiprows=13)
            rawdata_dataframe_without_dwelltimes = rawdata_dataframe.drop(index=0)
            rawdata_dataframe_without_dwelltimes_and_lastrow = rawdata_dataframe_without_dwelltimes.drop(
                columns=rawdata_dataframe.columns[-1])
            try:
                rawdata_dataframe_without_dwelltime_and_time = rawdata_dataframe_without_dwelltimes_and_lastrow.drop(
                    columns=rawdata_dataframe.columns[0])
            except KeyError:
                self.gui.notifications.notification_error(header='Data Type Error',
                                                          body='Your Sample Data does not match your chosen Data Type')
                return False
            rawdata_dataframe_without_time = rawdata_dataframe_without_dwelltime_and_time.apply(pd.to_numeric)
            sum = rawdata_dataframe_without_time.sum(axis=1)
            rawdata_dataframe_without_time['TIC'] = sum
            self.masses = list(rawdata_dataframe_without_time)
            sample_raw_data = rawdata_dataframe_without_dwelltimes_and_lastrow

            time_data_sample = rawdata_dataframe_without_dwelltimes['Time'].to_numpy()
            intensity_data_sample = rawdata_dataframe_without_time['TIC'].to_numpy()

        if data_type == 'EIC':
            column_names = []
            with open(self.directory) as f:
                df_info = pd.read_csv(f, sep=import_separator, skiprows=0, engine='python', nrows=2)
            header = df_info.columns
            for i in header:
                if 'Unnamed' in i:
                    continue
                else:
                    column_names.append(i)

            self.set_list_of_unique_masses_in_file(column_names[1:])

            with open(self.directory) as f:
                df = pd.read_csv(f, sep=import_separator, skiprows=1, engine='python', header=None)

            try:
                df.columns = column_names
            except ValueError:
                df.drop(columns=[df.columns[-1]], inplace=True)
                df.columns = column_names
            df.insert(0, 'Time', df['rt'] * 60)
            df = df.drop(columns=(['rt']))

            time_data_sample = df['Time'].to_numpy()

            eic_rawdata_dataframe_without_time = df.drop(
                columns=df.columns[0])
            eic_rawdata_dataframe_without_time = eic_rawdata_dataframe_without_time.apply(pd.to_numeric)
            sum = eic_rawdata_dataframe_without_time.sum(axis=1)
            eic_rawdata_dataframe_without_time['TIC'] = sum
            self.masses = list(eic_rawdata_dataframe_without_time)
            sample_raw_data = df
            intensity_data_sample = eic_rawdata_dataframe_without_time['TIC'].to_numpy()


        logfile_dataframe = self.gui.importer.import_laser_logfile(logfile=logfile,
                                                                   laser_type=laser,
                                                                   iolite_file=True,
                                                                   rectangular_data_calculation=False)
        if logfile_dataframe is False:
            return

        masked_array, inverted_mask, time_array, self.clean_time_array = mask_array(
            main_array=logfile_dataframe['Y(um)'].to_numpy(),
            mask_array=logfile_dataframe['Intended X(um)'].to_numpy(),
            on_value=(sum.max()) * 1.2,
            timestamp_array=logfile_dataframe['Timestamp'].to_numpy())


        self.import_separator = import_separator
        self.set_data_type(data_type)
        self.set_mask(inverted_mask)
        self.set_sample_array(logfile_dataframe['Comment'].dropna().to_numpy())
        self.set_sample_raw_data(sample_raw_data)
        self.tic_data = intensity_data_sample

        self.laser_log_time = time_array
        self.laser_log_status = masked_array
        self.time_data_sample = time_data_sample
        self.plot_laser_log_and_image_data(time=time_data_sample,
                                           intensity=intensity_data_sample)

        return True

    def set_data_type(self, data_type):
        self.data_type = data_type

    def set_mask(self, mask):
        self.logfile_mask = mask

    def set_sample_array(self, sample_array):
        self.samples = sample_array

    def set_sample_raw_data(self, raw_data):
        self.sample_rawdata = raw_data

    def set_list_of_unique_masses_in_file(self, list):
        self.list_of_unique_masses_in_file = list

    def get_data(self, sample_name):
        if sample_name == 'Full Data':
            return self.sample_data_dictionary, self.list_of_unique_masses_in_file, self.time_data_sample
        else:
            return self.sample_data_dictionary[sample_name], self.list_of_unique_masses_in_file, self.time_data_sample


if __name__ == "__main__":
    import main
    root = tk.Tk()
    root.iconbitmap("lassoimage.ico")
    main_app = main.MainApp(master_window=root)
    main_app.show_gui()

    main_app.gui.synchronizer.directory = 'C:/Users/j_sch220/PycharmProjects/NextGenerationLassoScript/Testdata/Gelatine_EIC_Triggerlos_only427_195.csv'
    main_app.gui.synchronizer.filename = 'Gelatine_EIC_Triggerlos_only427_195.csv'

    main_app.gui.synchronizer.synchronize_data(data_type='EIC', laser='Cetac G2+', import_separator=';', test=True,
                                               logfile='C:/Users/j_sch220/PycharmProjects/NextGenerationLassoScript/Testdata/Gelatineschnitt_log_Triggerlos.Iolite.csv')

    main_app.gui.synchronizer.toggle_window_visivility()

    tk.mainloop()


