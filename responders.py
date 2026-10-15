
class Responder:
    def __init__(self, responder_id, location, available=True):
        self.responder_id = responder_id
        self.location = location
        self.available = available

    def get_status(self):
        return "Available" if self.available else "Busy"


class Ambulance(Responder):
    responder_type = "Ambulance"

    def describe_duties(self):
        return "Provides emergency medical assistance."


class FireTruck(Responder):
    responder_type = "FireTruck"

    def describe_duties(self):
        return "Responds to fires and rescue operations."


class Police(Responder):
    responder_type = "Police"

    def describe_duties(self):
        return "Handles security and law enforcement."
