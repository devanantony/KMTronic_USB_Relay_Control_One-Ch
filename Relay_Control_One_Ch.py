import serial
import serial.tools.list_ports
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, scrolledtext

DESCRIPTION_FILE = "relay_descriptions.json"
PRODUCT_ID = "6001"  # USB Relay Product ID

def find_relay_ports():
    ports = serial.tools.list_ports.comports()
    relays = {}
    for port in ports:
        if PRODUCT_ID in port.hwid:
            relays[port.serial_number] = port.device
    return relays

def send_command(port, state):
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            ser.write(b'\xFF\x01' if state else b'\xFF\x00')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send command: {e}")

class RelayControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KMTronic Relay Controller")
        # DO NOT set geometry -> auto-size
        self.relay_ports = find_relay_ports()
        self.relay_frames = {}
        self.status_circles = {}
        self.relay_states = {}
        self.description_boxes = {}
        self.relay_descriptions = {}
        self.selected_com_port = tb.StringVar()

        self.load_descriptions()
        self.create_ui()
        self.root.update()  # ensure widgets are drawn
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())  # prevent shrinking too small

    def load_descriptions(self):
        import os, json
        if os.path.exists(DESCRIPTION_FILE):
            with open(DESCRIPTION_FILE, 'r') as f:
                self.relay_descriptions = json.load(f)

    def save_descriptions(self):
        import json
        with open(DESCRIPTION_FILE, 'w') as f:
            json.dump(self.relay_descriptions, f, indent=2)

    def create_ui(self):
        # COM port selection
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if ports:
            self.selected_com_port.set(ports[0])
        port_frame = tb.Frame(self.root)
        port_frame.pack(pady=10, padx=10, fill="x")

        tb.Label(port_frame, text="Select COM Port:").pack(side="left", padx=5)
        port_menu = tb.Combobox(port_frame, values=ports, textvariable=self.selected_com_port, width=20)
        port_menu.pack(side="left", padx=5)

        refresh_btn = tb.Button(port_frame, text="Refresh Ports", bootstyle=SUCCESS, command=self.refresh_ports)
        refresh_btn.pack(side="left", padx=5)

        # Relay rows
        for i, (serial_num, port) in enumerate(self.relay_ports.items()):
            frame = tb.Frame(self.root, padding=5)
            frame.pack(padx=10, pady=5, fill="x")

            # ON/OFF button
            btn = tb.Button(frame, text="OFF", width=8,
                            command=lambda sn=serial_num: self.toggle_relay(sn))
            btn.grid(row=0, column=0, padx=5, sticky="w")

            # Status circle
            canvas = tb.Canvas(frame, width=20, height=20)
            canvas.grid(row=0, column=1, padx=5)
            circle = canvas.create_oval(2, 2, 18, 18, fill="red")
            self.status_circles[serial_num] = (canvas, circle)
            self.relay_states[serial_num] = False

            # Description box
            desc_box = scrolledtext.ScrolledText(frame, width=60, height=2, wrap="word")
            desc_box.grid(row=0, column=2, padx=10)
            self.description_boxes[serial_num] = desc_box
            if serial_num in self.relay_descriptions:
                desc_box.insert("end", self.relay_descriptions[serial_num])

            # Save button
            save_btn = tb.Button(frame, text="Save", bootstyle=PRIMARY,
                                 command=lambda sn=serial_num: self.save_description(sn))
            save_btn.grid(row=0, column=3, padx=5)

            # Clear button
            clear_btn = tb.Button(frame, text="Clear", bootstyle=DANGER,
                                  command=lambda sn=serial_num: self.clear_description(sn))
            clear_btn.grid(row=0, column=4, padx=5)

            self.relay_frames[serial_num] = frame

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.selected_com_port.set(ports[0] if ports else "")
        messagebox.showinfo("Ports Refreshed", "Available COM ports updated.")

    def toggle_relay(self, serial_num):
        current_state = self.relay_states[serial_num]
        new_state = not current_state
        port = self.selected_com_port.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port first!")
            return
        send_command(port, new_state)
        self.relay_states[serial_num] = new_state
        self.update_ui(serial_num)

    def update_ui(self, serial_num):
        state = self.relay_states[serial_num]
        canvas, circle = self.status_circles[serial_num]
        canvas.itemconfig(circle, fill="green" if state else "red")

        btn = self.relay_frames[serial_num].winfo_children()[0]
        btn.config(text="ON" if state else "OFF")

    def save_description(self, serial_num):
        text = self.description_boxes[serial_num].get("1.0", "end").strip()
        self.relay_descriptions[serial_num] = text
        self.save_descriptions()
        messagebox.showinfo("Saved", f"Description for Relay {serial_num} saved.")

    def clear_description(self, serial_num):
        self.description_boxes[serial_num].delete("1.0", "end")
        if serial_num in self.relay_descriptions:
            del self.relay_descriptions[serial_num]
            self.save_descriptions()


if __name__ == "__main__":
    root = tb.Window(themename="flatly")  # Modern theme
    app = RelayControlApp(root)
    root.mainloop()
