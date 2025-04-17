import os
from datetime import datetime
import rticonnextdds_connector as Connector

# File paths
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

reader_map = {
    "radiology": "RadiologyReader",
    "pharmacy": "PharmacyReader",
    "emergency": "EmergencyReader",
    "laboratory": "LaboratoryReader"
}

writer_map = {
    "radiology": "RadiologyWriter",
    "pharmacy": "PharmacyWriter",
    "emergency": "EmergencyWriter",
    "laboratory": "LaboratoryWriter"
}

# --- User input ---
print("\n=== Staff Ticket Manager ===")
phone = input("Enter patient's phone number: ").strip()
department = input("Department (radiology/pharmacy/emergency/laboratory): ").strip().lower()
action = input("Action (call / complete): ").strip().lower()

if department not in reader_map or action not in ["call", "complete"]:
    print("❌ Invalid input.")
    exit()

# Connect to DDS
with Connector.open_connector(
        config_name="MyParticipantLibrary::HospitalParticipant",
        url=xml_path) as connector:
    reader = connector.get_input(f"MySubscriber::{reader_map[department]}")
    writer = connector.get_output(f"MyPublisher::{writer_map[department]}")

    print("\n📡 Searching for ticket...")

    # Get current data
    reader.wait()
    reader.take()

    found = False

    for sample in reader.samples.valid_data_iter:
        data = sample.get_dictionary()
        if data["phone"] == phone:
            found = True
            print(f"✅ Ticket found: {data['name']}")

            # Update the ticket
            writer.instance.set_string("name", data["name"])
            writer.instance.set_string("phone", data["phone"])
            writer.instance.set_string("department", data["department"])
            writer.instance.set_string("time_requested", data["time_requested"])
            writer.instance.set_string("status", "called" if action == "call" else "serviced")

            # Preserve previous call time if completing
            if action == "call":
                writer.instance.set_string("time_called", datetime.now().isoformat(timespec="seconds"))
                writer.instance.clear_member("time_completed")
            else:
                writer.instance.set_string("time_called", data.get("time_called", ""))
                writer.instance.set_string("time_completed", datetime.now().isoformat(timespec="seconds"))

            writer.write()
            print(f"🔄 Ticket updated with status '{action}'")

    if not found:
        print("❌ Ticket not found.")
