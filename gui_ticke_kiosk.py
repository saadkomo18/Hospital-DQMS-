import os
import tkinter as tk
from datetime import datetime
import rticonnextdds_connector as Connector

# DDS config
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

writer_map = {
    "Radiology": "RadiologyWriter",
    "Pharmacy": "PharmacyWriter",
    "Emergency": "EmergencyWriter",
    "Laboratory": "LaboratoryWriter"
}

# GUI App
class TicketKioskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Queue Kiosk")

        from rticonnextdds_connector import Connector
        self.connector = Connector("MyParticipantLibrary::HospitalParticipant", "HospitalConfig.xml")
        self.writer_map = {
            "Radiology": self.connector.get_output("MyPublisher::RadiologyWriter"),
            "Pharmacy": self.connector.get_output("MyPublisher::PharmacyWriter"),
            "Emergency": self.connector.get_output("MyPublisher::EmergencyWriter"),
            "Laboratory": self.connector.get_output("MyPublisher::LaboratoryWriter")
        }
        self.root.geometry("500x500")
        # self.root.attributes('-fullscreen', True)

        self.build_interface()
        self.clear_confirmation()

    def build_interface(self):
        # Header
        tk.Label(self.root, text="🏥 Welcome to Hospital Kiosk", font=("Arial", 18, "bold")).pack(pady=20)

        # Name
        tk.Label(self.root, text="👤 Name:", font=("Arial", 12)).pack()
        self.entry_name = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.entry_name.pack(pady=8)

        # Phone
        tk.Label(self.root, text="📱 Phone Number:", font=("Arial", 12)).pack()
        self.entry_phone = tk.Entry(self.root, font=("Arial", 12), width=30, fg="gray")
        self.entry_phone.insert(0, "05xxxxxxxx")
        self.entry_phone.bind("<FocusIn>", self.clear_phone_hint)
        self.entry_phone.bind("<FocusOut>", self.restore_phone_hint)
        self.entry_phone.pack(pady=8)

        # Department
        tk.Label(self.root, text="🏥 Select Department:", font=("Arial", 12)).pack()
        self.department_var = tk.StringVar()
        self.department_var.set("Radiology")
        self.dept_menu = tk.OptionMenu(self.root, self.department_var, *writer_map.keys())
        self.dept_menu.config(font=("Arial", 12), width=20)
        self.dept_menu.pack(pady=8)

        # Submit Button
        tk.Button(
            self.root,
            text="Submit Ticket",
            command=self.submit_ticket,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 13, "bold"),
            width=20
        ).pack(pady=25)

        # Confirmation Area
        self.confirm_label = tk.Label(self.root, text="", font=("Arial", 12), fg="green", justify="center")
        self.confirm_label.pack(pady=10)

    def clear_confirmation(self):
        self.confirm_label.config(text="")

    def clear_phone_hint(self, event):
        if self.entry_phone.get() == "05xxxxxxxx":
            self.entry_phone.delete(0, tk.END)
            self.entry_phone.config(fg="black")

    def restore_phone_hint(self, event):
        if not self.entry_phone.get():
            self.entry_phone.insert(0, "05xxxxxxxx")
            self.entry_phone.config(fg="gray")

    def submit_ticket(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        dept = self.department_var.get()

        if phone == "05xxxxxxxx":
            phone = ""

        if not name or not phone:
            self.confirm_label.config(text="❌ Please enter name and phone.", fg="red")
            return

        if not (phone.isdigit() and len(phone) == 10 and phone.startswith("05")):
            self.confirm_label.config(text="❌ Phone must be 10 digits and start with 05.", fg="red")
            return

        time_requested = datetime.now().isoformat(timespec="seconds")

        try:
            writer = self.connector.get_output(f"MyPublisher::{writer_map[dept]}")
            writer.instance.set_string("name", name)
            writer.instance.set_string("phone", phone)
            writer.instance.set_string("department", dept.lower())
            writer.instance.set_string("status", "waiting")
            writer.instance.set_string("time_requested", time_requested)
            writer.instance.clear_member("time_called")
            writer.instance.clear_member("time_completed")
            writer.write()

            confirmation_text = (
                f"✅ Ticket Submitted!\n\n"
                f"📍 Department: {dept}\n"
                f"🕓 {time_requested}"
            )
            self.confirm_label.config(text=confirmation_text, fg="green")

            self.entry_name.delete(0, tk.END)
            self.entry_phone.delete(0, tk.END)
            self.restore_phone_hint(None)

            self.root.after(5000, self.clear_confirmation)

        except Exception as e:
            self.confirm_label.config(text=f"DDS Error: {e}", fg="red")

# Run it
if __name__ == "__main__":
    root = tk.Tk()
    app = TicketKioskApp(root)
    root.mainloop()
