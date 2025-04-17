import os
from datetime import datetime
import rticonnextdds_connector as Connector
from time import sleep

# File path (make sure HospitalConfig.xml is in the same folder)
file_path = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.join(file_path, "HospitalConfig.xml")

with Connector.open_connector(
        config_name="MyParticipantLibrary::HospitalParticipant",
        url=file_path + "/HospitalConfig.xml") as connector:

        writer = connector.get_output("MyPublisher::RadiologyWriter")
        
        for i in range(1, 100):
            writer.instance.set_string("name", "saad")
            writer.instance.set_string("phone", "0505342561")
            writer.instance.set_string("department", "Radiology")
            writer.instance.set_string("status", "waiting")
            writer.instance.set_string("time_requested", "now")

            writer.instance.clear_member("time_called")
            writer.instance.clear_member("time_completed")

            writer.write()
            print(f"\n✅ Ticket submitted ")
            sleep(0.5)