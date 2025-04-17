import os
from datetime import datetime
import rticonnextdds_connector as Connector

# File path (make sure HospitalConfig.xml is in the same folder)
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

# Department to writer mapping
writer_map = {
    "radiology": "RadiologyWriter",
    "pharmacy": "PharmacyWriter",
    "emergency": "EmergencyWriter",
    "laboratory": "LaboratoryWriter"
}

# User input
print("\n=== Hospital Ticket Kiosk ===")
name = input("👤 Enter your name: ").strip()
phone = input("📱 Enter your phone number: ").strip()

print("\n🏥 Departments:")
for d in writer_map.keys():
    print(f" - {d.capitalize()}")
department = input("Select a department: ").strip().lower()

if department not in writer_map:
    print("❌ Invalid department selected.")
    exit()

# Time of ticket request
time_requested = datetime.now().isoformat(timespec="seconds")

# Connect to DDS and publish the ticket
with Connector.open_connector(
        config_name="MyParticipantLibrary::HospitalParticipant",
        url=file_path + "/HospitalConfig.xml") as connector:

        writer = connector.get_output(f"MyPublisher::{writer_map[department]}")
        
        writer.instance.set_string("name", name)
        writer.instance.set_string("phone", phone)
        writer.instance.set_string("department", department)
        writer.instance.set_string("status", "waiting")
        writer.instance.set_string("time_requested", time_requested)

        writer.instance.clear_member("time_called")
        writer.instance.clear_member("time_completed")

        writer.write()
        print(f"\n✅ Ticket submitted to {department.capitalize()} at {time_requested}")
