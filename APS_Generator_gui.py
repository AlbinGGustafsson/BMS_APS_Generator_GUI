import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from functools import partial
import xml.dom.minidom


from nturl2path import pathname2url
import sys
from time import time
import os

show_xml_file = 1

active_input        = 1
comments_aps        = 0
advanced_mode       = 1
filename_from_arg   = 0
version             = "v0.2"

class parameter:
    id              =   2,   4,  5,  6,   7,  8,  9, 10, 11, 12, 13,  14,  15,  17,  18, 19, 20, 21, 22, 23, 24
    pre_value       =  15,  23, 13,  2, 420,  1,  1,  8,  0,  2,  0,  15,   5, 260,   0,  1,  0,  0,  0,  0, 0
    min_limit       =   0,   0,  6,  1,  50,  0,  0,  1,  0,  0,  0,   0,   0,   0,   0,  0,  0,  0,  0,  0, 0
    max_limit       = 999, 999, 26,  4, 840,  1,  1,  8,  4,  4,  3, 999, 999, 999,   1,  4,  1,  1,  1,  1, 1
    default_value   =  21,   0,  7,  1, 210,  0,  0,  8,  2,  0,  0,  15,   5, 260,   0,  1,  0,  0,  0,  0, 0
    advanced_par    =   0,   0,  0,  0,   0,  1,  1,  0,  0,  0,  0,   1,   1,   1,   1,  0,  0,  1,  1,  1, 1
    question        = [
        "Power package version (default 21): ",
        "Config number (default 0): ",
        "Modules in series (default 7): ",
        "Modules in parallel (default 1): ",
        "Total capacity (default 210): ",
        "Heater enabled (default 0): ",
        "Q-Sense enabled (default 0): ",
        "Charge speed (c-rate x10)(default 8): ",
        "Cell-type (0 = 29E7 *default, 2 = 48X, 4 = 33V): ",
        "Charge type (0 = No charger, 1 = On board, 2 = External *default*, 3 = Auto, 4 = Master CAN with Pilot): ",
        "Truck type (0 = Integrated *default*, 1 = Standalone, 2 = Standalone with indicator, 3 = Toyota Gen2): ",
        "HC Unlock trigger (default 15): ",
        "HC Unlock release (default 5): ",
        "AUX Harware charge parameter (default 260): ",
        "Charger in battery compartment (default 0): ",
        "Baudrate (1 = 125kbps *default*, 2 = 250kbps, 3 = 500kbps, 4 = 1Mbps: ",
        "Charger connector (0 = Lejon *default*, 1 = Kobra): ",
        "Configuration method (0 = Strömberg *default*, 1 = Truck assembly): ",
        "CAN current sensor enabled (default 0): ",
        "Dual contactor dedicated enabled (default 0): ",
        "Extended CAN (PDO3) enabled (default 0): "
    ]

class APSCreatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("APS-file generator " + version)
        #self.geometry("700x850")

        # Variables for the GUI
        self.entries = {}
        self.show_xml_file_var = tk.IntVar(value=show_xml_file)
        self.advanced_mode_var = tk.IntVar(value=advanced_mode)
        self.comments_aps_var = tk.IntVar(value=comments_aps)
        self.filename_var = tk.StringVar(value="")

        # Create GUI components
        self.create_widgets()

    def create_widgets(self):
        # Checkboxes for flags
        ttk.Checkbutton(self, text="Show XML File", variable=self.show_xml_file_var).pack(padx=10, pady=5)
        ttk.Checkbutton(self, text="Advanced Mode", variable=self.advanced_mode_var).pack(padx=10, pady=5)
        ttk.Checkbutton(self, text="Comments in APS", variable=self.comments_aps_var).pack(padx=10, pady=5)

        # Entry for Serial Number
        serial_frame = ttk.Frame(self)
        serial_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(serial_frame, text="Serial Number: ").pack(side=tk.LEFT)
        self.serial_var = tk.StringVar()
        # Assigning the Entry widget to self.serial_entry
        self.serial_entry = ttk.Entry(serial_frame, textvariable=self.serial_var)
        self.serial_entry.pack(side=tk.LEFT, fill=tk.X)
        # Set the focus to the serial number entry
        self.serial_entry.focus()


        # Entries for parameters
        for i, question in enumerate(parameter.question):
            frame = ttk.Frame(self)
            frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(frame, text=question).grid(row=i, column=0, sticky=tk.W)
            entry_var = tk.StringVar(value=str(parameter.default_value[i]))
            entry = ttk.Entry(frame, textvariable=entry_var)
            entry.grid(row=i, column=1)
            # Binding the Enter key to the set_default_value function
            entry.bind('<Return>', lambda event, idx=i: self.set_default_value(event, idx))
            self.entries[i] = entry

        # Submit button
        ttk.Button(self, text="Generate", command=self.generate_aps_file).pack(padx=10, pady=20)

    def set_default_value(self, event, idx):
        """Set the default value for the entry when Enter key is pressed and move to the next widget."""
        event.widget.delete(0, tk.END)  # Clear the existing value
        event.widget.insert(0, str(parameter.default_value[idx]))  # Insert the default value

        # Set focus to the next widget
        if idx + 1 in self.entries:  # Check if the next index exists
            next_widget = self.entries[idx + 1]
            next_widget.focus()
            next_widget.select_range(0, tk.END)  # Select all text in the next widget for easy overwrite


    def reset_fields(self):
        # Clear the serial number field
        self.serial_var.set("")
        
        # Clear parameter fields and set to default values
        for i, entry_var in self.entries.items():
            entry_var.delete(0, tk.END)

    def generate_aps_file(self):
        # Collect parameter values from the UI entries
        par = []
        
        for i in range(len(parameter.id)):
            # If not in advanced mode and the parameter is advanced, use the default value
            if not self.advanced_mode_var.get() and parameter.advanced_par[i]:
                par.append(parameter.default_value[i])
                continue

            # Check if the entered value is a valid integer within the allowed range
            try:
                inp = int(self.entries[i].get())
                if inp < parameter.min_limit[i] or inp > parameter.max_limit[i]:
                    messagebox.showerror("Error", f"The value for {parameter.question[i]} is outside limits. Allowed range is: {parameter.min_limit[i]} - {parameter.max_limit[i]}")
                    return
                else:
                    par.append(inp)
            except ValueError:
                messagebox.showerror("Error", f"Please enter a valid integer for {parameter.question[i]}")
                return

        # Use the serial number as the filename
        serial_number = self.serial_var.get().strip()
        if not serial_number:
            messagebox.showerror("Error", "Please provide a serial number.")
            return

        file_path = os.path.join(os.getcwd(), f"{serial_number}_BP")  # Save in the same folder where the script is located

        # Write to the APS file
        with open(file_path, "w") as f:
            # APS file header
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?><Truck package=\"7623820-")
            if par[0] < 100:
                f.write("0")
            f.write(str(par[0]))
            f.write("\" class=\"TruckCom.App.BMSTruck\"><Node name=\"BMS\" canId=\"0\" downloadId=\"0\" file=\"0000000-000.xml\" class=\"TruckCom.App.BMS3\" needsKeyRelay=\"false\">")

            ipar = 0
            ival = 0
            while ipar < len(parameter.id) + 3:
                # Handle specific package and config bases separately
                if ipar == 0:
                    f.write("<Parameter id=\"1\" value=\"7623820\" />")
                    ipar += 1
                    continue
                if ipar == 2:
                    f.write("<Parameter id=\"3\" value=\"7623507\" />")
                    ipar += 1
                    continue
                if ipar == 16 - 1:
                    ipar += 1
                    continue

                # Write the APS file comments if the option is selected
                if self.comments_aps_var.get():
                    f.write("<!--")
                    f.write(parameter.question[ival])
                    f.write("-->")
                f.write("<Parameter id=\"")
                f.write(str(ipar + 1))
                f.write("\" value=\"")
                f.write(str(par[ival]))
                f.write("\" />")
                ipar += 1
                ival += 1

            f.write("</Node></Truck>")

        messagebox.showinfo("Success", f"APS file saved as {serial_number}_BP")
        self.reset_fields()
        self.serial_entry.focus()

        if self.show_xml_file_var.get():
            self.show_xml_content(file_path)


    def show_xml_content(self, file_path):
        # Open the XML file and read its content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse and pretty print the XML content
        parsed_xml = xml.dom.minidom.parseString(content)
        pretty_xml = parsed_xml.toprettyxml()

        # Create a new Toplevel window
        xml_window = tk.Toplevel(self)
        xml_window.title("XML Content")
        xml_window.geometry("1000x500")

        # Create a Frame to hold the Text widget and Scrollbars
        frame = tk.Frame(xml_window)
        frame.pack(expand=True, fill=tk.BOTH)

        # Add Scrollbars
        scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y = ttk.Scrollbar(frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Add a Text widget to display the XML
        xml_text_widget = tk.Text(frame, wrap=tk.NONE, xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        xml_text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Configure scrollbars to scroll the Text widget
        scroll_x.config(command=xml_text_widget.xview)
        scroll_y.config(command=xml_text_widget.yview)

        # Insert the formatted XML content into the Text widget
        xml_text_widget.insert(tk.END, pretty_xml)

if __name__ == "__main__":
    app = APSCreatorGUI()
    app.mainloop()