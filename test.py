import rticonnextdds_connector as Connector
import time
import os

# File path (make sure HospitalConfig.xml is in the same folder)
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

with Connector.open_connector(
        config_name="MyParticipantLibrary::HospitalParticipant",
        url=file_path + "/HospitalConfig.xml") as connector:
      reader = connector.get_input("MySubscriber::RadiologyReader")

      print("📡 Waiting for DDS data...")
      while True:
        reader.read()
        for sample in reader.samples.valid_data_iter:
            print("🎟 Ticket received:", sample.get_dictionary())
        time.sleep(1)
