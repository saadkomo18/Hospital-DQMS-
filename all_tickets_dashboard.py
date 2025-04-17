import os
import tkinter as tk
from datetime import datetime
from rticonnextdds_connector import Connector
from collections import defaultdict

# DDS setup
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

readers = {
    "Radiology": "RadiologyReader",
    "Pharmacy": "PharmacyReader",
    "Emergency": "EmergencyReader",
    "Laboratory": "LaboratoryReader"
}

STATUS_COLORS = {
    "waiting": "orange",
    "called": "blue",
    "serviced": "gray"
}

class AllTicketsDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 All Tickets Dashboard")
        self.root.geometry("900x600")

        # Stats Frame
        self.stats_frame = tk.Frame(root)
        self.stats_frame.pack(fill=tk.X, pady=10)

        # Scrollable Ticket List
        canvas = tk.Canvas(root)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # DDS Setup
        self.tickets = {}
        self.connector = Connector("MyParticipantLibrary::HospitalParticipant", xml_path)
        self.readers = {dept: self.connector.get_input(f"MySubscriber::{r}") for dept, r in readers.items()}

        self.build_table()
        self.refresh()

    def build_table(self):
        # Clear both frames
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # -------------------------
        # 📊 Stats Panel
        # -------------------------
        stats = defaultdict(lambda: defaultdict(int))
        for ticket in self.tickets.values():
            dept = ticket.get("department", "").capitalize()
            status = ticket.get("status", "").lower()
            stats[dept][status] += 1
            stats[dept]["total"] += 1

        tk.Label(self.stats_frame, text="📊 Live Ticket Stats", font=("Arial", 14, "bold")).pack()

        for dept, counts in stats.items():
            text = f"• {dept}:  "
            for status in ["waiting", "called", "serviced"]:
                count = counts.get(status, 0)
                text += f"{status.capitalize()}={count}  "
            tk.Label(self.stats_frame, text=text, font=("Arial", 10), fg="darkblue").pack(anchor="w")

        # -------------------------
        # 🧾 Ticket Table
        # -------------------------
        headers = ["Name", "Phone", "Department", "Status", "Time Requested"]
        for i, h in enumerate(headers):
            tk.Label(self.scroll_frame, text=h, font=("Arial", 10, "bold")).grid(row=0, column=i, padx=10, pady=6)

        sorted_tickets = sorted(
            self.tickets.values(),
            key=lambda x: x.get("time_requested", ""),
        )

        for idx, data in enumerate(sorted_tickets, start=1):
            status = data.get("status", "").lower()
            color = STATUS_COLORS.get(status, "black")

            tk.Label(self.scroll_frame, text=data.get("name", ""), font=("Arial", 10)).grid(row=idx, column=0)
            tk.Label(self.scroll_frame, text=data.get("phone", ""), font=("Arial", 10)).grid(row=idx, column=1)
            tk.Label(self.scroll_frame, text=data.get("department", ""), font=("Arial", 10)).grid(row=idx, column=2)
            tk.Label(
                self.scroll_frame,
                text=status,
                fg="white",
                bg=color,
                font=("Arial", 10, "bold"),
                width=10
            ).grid(row=idx, column=3, padx=5, pady=2)
            tk.Label(self.scroll_frame, text=data.get("time_requested", ""), font=("Arial", 10)).grid(row=idx, column=4)

    def refresh(self):
        try:
            for dept, reader in self.readers.items():
                reader.read()
                for sample in reader.samples.valid_data_iter:
                    d = sample.get_dictionary()
                    self.tickets[d["phone"]] = d
                    print(f"📥 {d['department']} - {d['name']} ({d['status']})")
        except Exception as e:
            print(f"⚠️ DDS Error: {e}")

        self.build_table()
        self.root.after(3000, self.refresh)

# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = AllTicketsDashboard(root)
    root.mainloop()
