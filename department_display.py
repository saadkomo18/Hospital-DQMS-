import os
from time import sleep
import rticonnextdds_connector as Connector

# Config paths
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

# Choose department/topic to display
department = input("Enter department to monitor (radiology/pharmacy/emergency/laboratory): ").lower().strip()

reader_map = {
    "radiology": "RadiologyReader",
    "pharmacy": "PharmacyReader",
    "emergency": "EmergencyReader",
    "laboratory": "LaboratoryReader"
}

if department not in reader_map:
    print("❌ Invalid department.")
    exit()

with Connector.open_connector(
        config_name="MyParticipantLibrary::HospitalParticipant",
        url=xml_path) as connector:

    reader = connector.get_input(f"MySubscriber::{reader_map[department]}")
    print(f"\n📺 Monitoring department: {department.capitalize()} (press Ctrl+C to stop)\n")

    try:
        while True:
            reader.wait()  # Wait for new data
            reader.take()  # Take all available data

            for sample in reader.samples.valid_data_iter:
                data = sample.get_dictionary()
                print("🆕 New Ticket Received")
                print(f" - Name      : {data['name']}")
                print(f" - Phone     : {data['phone']}")
                print(f" - Status    : {data['status']}")
                print(f" - Requested : {data['time_requested']}")
                print("-" * 30)

            sleep(0.2)

    except KeyboardInterrupt:
        print("\n🛑 Stopped monitoring.")
