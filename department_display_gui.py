import os
import tkinter as tk
from datetime import datetime
from rticonnextdds_connector import Connector

# DDS setup
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

reader_map = {
    "Radiology": "RadiologyReader",
    "Pharmacy": "PharmacyReader",
    "Emergency": "EmergencyReader",
    "Laboratory": "LaboratoryReader"
}

writer_map = {
    "Radiology": "RadiologyWriter",
    "Pharmacy": "PharmacyWriter",
    "Emergency": "EmergencyWriter",
    "Laboratory": "LaboratoryWriter"
}

class DepartmentDisplayGUI:
    def __init__(self, root, department):
        self.root = root
        self.department = department
        self.root.title(f"{department} - Department Action Panel")
        self.root.geometry("800x600")

        self.connector = Connector("MyParticipantLibrary::HospitalParticipant", xml_path)
        self.reader = self.connector.get_input(f"MySubscriber::{reader_map[department]}")
        self.writer = self.connector.get_output(f"MyPublisher::{writer_map[department]}")

        self.tickets = {}

        self.header = tk.Label(
            self.root,
            text=f"🩺 Department: {department}",
            font=("Arial", 18, "bold")
        )
        self.header.pack(pady=15)

        # Scrollable area
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.ticket_frame = tk.Frame(canvas)

        self.ticket_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.ticket_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh()

    def refresh(self):
        try:
            self.reader.read()
            for sample in self.reader.samples.valid_data_iter:
                data = sample.get_dictionary()
                if data["status"] != "serviced" and data["department"].lower() == self.department.lower():
                    print(f"📥 Received: {data['phone']} status={data['status']}")
                if data["status"].lower() != "serviced":
                    self.tickets[data["phone"]] = data
                elif data["phone"] in self.tickets:
                    del self.tickets[data["phone"]]
        except Exception as e:
            print(f"⚠️ DDS Error: {e}")

        self.render_table()
        self.root.after(3000, self.refresh)

    def render_table(self):
        for widget in self.ticket_frame.winfo_children():
            widget.destroy()

        headers = ["Name", "Phone", "Status", "Requested", "Actions"]
        for i, h in enumerate(headers):
            tk.Label(self.ticket_frame, text=h, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=10, pady=10)

        for idx, (phone, data) in enumerate(self.tickets.items(), start=1):
            status = data.get("status", "").capitalize()

            tk.Label(self.ticket_frame, text=data.get("name", ""), font=("Arial", 11)).grid(row=idx, column=0)
            tk.Label(self.ticket_frame, text=phone, font=("Arial", 11)).grid(row=idx, column=1)
            tk.Label(self.ticket_frame, text=status, font=("Arial", 11)).grid(row=idx, column=2)
            tk.Label(self.ticket_frame, text=data.get("time_requested", ""), font=("Arial", 11)).grid(row=idx, column=3)

            btn_frame = tk.Frame(self.ticket_frame)
            btn_frame.grid(row=idx, column=4, padx=5)

            def make_call_button(p):
                return lambda: self.update_ticket(p, "called")

            def make_complete_button(p):
                return lambda: self.update_ticket(p, "serviced")

            if data["status"] == "waiting":
                tk.Button(
                    btn_frame,
                    text="Call",
                    font=("Arial", 10, "bold"),
                    bg="#FFA500",
                    fg="white",
                    relief="flat",
                    borderwidth=0,
                    padx=10,
                    pady=5,
                    command=make_call_button(phone)
                ).pack(side=tk.LEFT, padx=5)

            if data["status"] in ["waiting", "called"]:
                tk.Button(
                    btn_frame,
                    text="Complete",
                    font=("Arial", 10, "bold"),
                    bg="#4CAF50",
                    fg="white",
                    relief="flat",
                    borderwidth=0,
                    padx=10,
                    pady=5,
                    command=make_complete_button(phone)
                ).pack(side=tk.LEFT, padx=5)

    def update_ticket(self, phone, new_status):
        data = self.tickets.get(phone)
        if not data:
            return

        now = datetime.now().isoformat(timespec="seconds")

        self.writer.instance.set_string("name", data["name"])
        self.writer.instance.set_string("phone", data["phone"])
        self.writer.instance.set_string("department", data["department"])
        self.writer.instance.set_string("time_requested", data["time_requested"])

        if new_status == "called":
            self.writer.instance.set_string("time_called", now)
            self.writer.instance.clear_member("time_completed")
        elif new_status == "serviced":
            self.writer.instance.set_string("time_called", data.get("time_called", now))
            self.writer.instance.set_string("time_completed", now)

        self.writer.instance.set_string("status", new_status)
        self.writer.write()

        if new_status == "serviced":
            self.tickets.pop(phone, None)

        self.render_table()

# Startup screen
def select_department():
    root = tk.Tk()
    root.title("Select Department")

    tk.Label(root, text="Choose Department", font=("Arial", 14)).pack(pady=10)
    selected = tk.StringVar(root)
    selected.set("Radiology")
    tk.OptionMenu(root, selected, *reader_map.keys()).pack(pady=5)

    def start_app():
        dept = selected.get()
        for widget in root.winfo_children():
            widget.destroy()
        DepartmentDisplayGUI(root, dept)

    tk.Button(root, text="Start", command=start_app, font=("Arial", 12, "bold")).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    select_department()
