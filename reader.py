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
        
        input = connector.get_input("MySubscriber::RadiologyReader")
        while True:
            input.wait()
            input.take()
            for sample in input.samples.valid_data_iter:
                data = sample.get_dictionary()
                print("name: " + data['name'])
                print("phone: " + data['phone'])