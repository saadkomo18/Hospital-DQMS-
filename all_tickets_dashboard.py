import tkinter as tk
from rticonnextdds_connector import Connector
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class AllTicketsDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Hospital Ticket Dashboard")
        self.root.geometry("1000x850")
        self.root.configure(bg="#f4f6f8")

        self.xml_path = "HospitalConfig.xml"
        self.connector = Connector("MyParticipantLibrary::HospitalParticipant", self.xml_path)

        self.readers = {
            "Radiology": self.connector.get_input("MySubscriber::RadiologyReader"),
            "Pharmacy": self.connector.get_input("MySubscriber::PharmacyReader"),
            "Emergency": self.connector.get_input("MySubscriber::EmergencyReader"),
            "Laboratory": self.connector.get_input("MySubscriber::LaboratoryReader")
        }

        self.tickets = {}
        self.selected_department = tk.StringVar(value="All")
        self.sort_order = tk.StringVar(value="Newest First")
        self.selected_status = tk.StringVar(value="All")

        # Header
        top_bar = tk.Frame(self.root, bg="#3f51b5")
        top_bar.pack(fill="x")
        title = tk.Label(top_bar, text="Hospital Queue Dashboard", font=("Arial", 18, "bold"), fg="white", bg="#3f51b5")
        title.pack(padx=10, pady=10)

        # Filters
        filter_frame = tk.Frame(self.root, bg="#f4f6f8")
        filter_frame.pack(pady=(10, 5))

        tk.Label(filter_frame, text="Department:", font=("Arial", 12), bg="#f4f6f8").pack(side="left", padx=5)
        dept_menu = tk.OptionMenu(filter_frame, self.selected_department, "All", *self.readers.keys())
        dept_menu.config(font=("Arial", 11, "bold"), relief="flat", bg="#e0e0e0", fg="#000", activebackground="#d5d5d5", highlightthickness=1, highlightbackground="#bdbdbd")
        dept_menu["menu"].config(font=("Arial", 11))
        dept_menu.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Sort by Time:", font=("Arial", 12), bg="#f4f6f8").pack(side="left", padx=10)
        sort_menu = tk.OptionMenu(filter_frame, self.sort_order, "Newest First", "Oldest First")
        sort_menu.config(font=("Arial", 11, "bold"), relief="flat", bg="#e0e0e0", fg="#000", activebackground="#d5d5d5", highlightthickness=1, highlightbackground="#bdbdbd")
        sort_menu["menu"].config(font=("Arial", 11))
        sort_menu.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Status:", font=("Arial", 12), bg="#f4f6f8").pack(side="left", padx=10)
        status_menu = tk.OptionMenu(filter_frame, self.selected_status, "All", "Waiting", "Called", "Serviced")
        status_menu.config(font=("Arial", 11, "bold"), relief="flat", bg="#e0e0e0", fg="#000", activebackground="#d5d5d5", highlightthickness=1, highlightbackground="#bdbdbd")
        status_menu["menu"].config(font=("Arial", 11))
        status_menu.pack(side="left", padx=5)

        self.summary_label = tk.Label(self.root, text="", font=("Arial", 13, "bold"), fg="#333", bg="#f4f6f8")
        self.summary_label.pack(pady=10)

        self.table_frame = tk.Frame(self.root, bg="white", padx=10, pady=10)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.chart_frame = tk.Frame(self.root, bg="#f4f6f8")
        self.chart_frame.pack(pady=10)
        self.bar_canvas = None
        self.pie_canvas = None

        self.render_table()
        self.refresh()

    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Phone", "Name", "Department", "Status", "Time Requested", "Time Called", "Time Completed", "Service Time (sec)"]
        for col, header in enumerate(headers):
            label = tk.Label(self.table_frame, text=header, font=("Arial", 12, "bold"),
                             borderwidth=1, relief="solid", padx=6, pady=4,
                             bg="#eceff1", highlightbackground="#ccc", highlightthickness=1)
            label.grid(row=0, column=col, sticky="nsew")

        dept_filter = self.selected_department.get()
        status_filter = self.selected_status.get()
        sort_order = self.sort_order.get()

        filtered = []
        for t in self.tickets.values():
            if dept_filter != "All" and t.get("department", "").lower() != dept_filter.lower():
                continue
            if status_filter != "All" and t.get("status", "").lower() != status_filter.lower():
                continue
            filtered.append(t)

        def get_time_requested(t):
            try:
                return datetime.fromisoformat(t.get("time_requested", ""))
            except:
                return datetime.min

        filtered = sorted(filtered, key=get_time_requested, reverse=(sort_order == "Newest First"))

        for row, data in enumerate(filtered, start=1):
            for col, key in enumerate(["phone", "name", "department", "status", "time_requested", "time_called", "time_completed"]):
                value = data.get(key, "")
                kwargs = {
                    "font": ("Arial", 11),
                    "borderwidth": 1,
                    "relief": "solid",
                    "padx": 6,
                    "pady": 4,
                    "highlightbackground": "#ccc",
                    "highlightthickness": 1
                }
                if key == "status":
                    status = value.lower()
                    if status == "waiting":
                        kwargs["bg"] = "#fbc02d"
                    elif status == "called":
                        kwargs["bg"] = "#66bb6a"
                    elif status == "serviced":
                        kwargs["bg"] = "#ef5350"
                label = tk.Label(self.table_frame, text=value, **kwargs)
                label.grid(row=row, column=col, sticky="nsew")

            try:
                t_requested = datetime.fromisoformat(data.get("time_requested"))
                t_completed = datetime.fromisoformat(data.get("time_completed")) if data.get("time_completed") else None
                if t_completed:
                    service_time = int((t_completed - t_requested).total_seconds())
                else:
                    service_time = ""
            except:
                service_time = ""

            label = tk.Label(self.table_frame, text=service_time, font=("Arial", 11), borderwidth=1, relief="solid",
                             padx=6, pady=4, highlightbackground="#ccc", highlightthickness=1)
            label.grid(row=row, column=7, sticky="nsew")

    def update_charts(self):
        if self.bar_canvas:
            self.bar_canvas.get_tk_widget().destroy()
        if self.pie_canvas:
            self.pie_canvas.get_tk_widget().destroy()

        dept_counts = {}
        status_counts = {"waiting": 0, "called": 0, "serviced": 0}
        for t in self.tickets.values():
            dept = t.get("department", "Unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
            s = t.get("status", "").lower()
            if s in status_counts:
                status_counts[s] += 1

        fig1, ax1 = plt.subplots(figsize=(4, 3))
        ax1.bar(dept_counts.keys(), dept_counts.values(), color="#42a5f5")
        ax1.set_title("Tickets per Department")

        self.bar_canvas = FigureCanvasTkAgg(fig1, master=self.chart_frame)
        self.bar_canvas.draw()
        self.bar_canvas.get_tk_widget().pack(side="left", padx=10)

        fig2, ax2 = plt.subplots(figsize=(4, 3))
        labels = []
        sizes = []
        colors = []

        for status, count in status_counts.items():
            if count > 0:
                labels.append(status)
                sizes.append(count)
                if status == "waiting":
                    colors.append("#fbc02d")
                elif status == "called":
                    colors.append("#66bb6a")
                elif status == "serviced":
                    colors.append("#ef5350")

        if sizes:
            ax2.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors)
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=12)

        ax2.set_title("Status Distribution")
        self.pie_canvas = FigureCanvasTkAgg(fig2, master=self.chart_frame)
        self.pie_canvas.draw()
        self.pie_canvas.get_tk_widget().pack(side="right", padx=10)

    def refresh(self):
        for dept, reader in self.readers.items():
            reader.read()
            for sample in reader.samples.valid_data_iter:
                data = sample.get_dictionary()
                self.tickets[data["phone"]] = data

        total_waiting = total_called = total_serviced = 0
        total_service_time = 0
        completed_count = 0

        for t in self.tickets.values():
            status = t.get("status", "").lower()
            if status == "waiting":
                total_waiting += 1
            elif status == "called":
                total_called += 1
            elif status == "serviced":
                total_serviced += 1

            try:
                if t.get("time_completed"):
                    t1 = datetime.fromisoformat(t["time_requested"])
                    t2 = datetime.fromisoformat(t["time_completed"])
                    total_service_time += int((t2 - t1).total_seconds())
                    completed_count += 1
            except:
                pass

        avg_service = total_service_time // completed_count if completed_count > 0 else 0
        self.summary_label.config(
            text=f"🧾 Waiting: {total_waiting} | Called: {total_called} | Serviced: {total_serviced} | Avg Service Time: {avg_service}s"
        )

        self.render_table()
        self.update_charts()
        self.root.after(3000, self.refresh)

if __name__ == "__main__":
    root = tk.Tk()
    app = AllTicketsDashboard(root)
    root.mainloop()
