class InvalidResponderException(Exception):
    pass


class Responder:
    responder_type = "Responder"
    VALID_STATUSES = ["available", "busy", "offline"]

    def __init__(self, responder_id, location, available=True, status=None):
        self.responder_id = responder_id
        self.location = location
        if status is not None:
            self.set_status(status)
        else:
            self.set_status("available" if available else "busy")

    def set_status(self, status):
        cleaned = str(status).strip().lower()
        if cleaned not in Responder.VALID_STATUSES:
            raise InvalidResponderException(
                f"Status must be one of: {', '.join(Responder.VALID_STATUSES)}."
            )
        self._status = cleaned

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self.set_status(value)

    @property
    def available(self):
        return self._status == "available"

    @available.setter
    def available(self, value):
        self.set_status("available" if value else "busy")

    @property
    def id(self):
        return self.responder_id

    @property
    def type(self):
        return self.responder_type

    def get_status(self):
        return self._status.capitalize()

    def describe_duties(self):
        return "General emergency response duties."

    def to_dict(self):
        return {
            "responder_id": self.responder_id,
            "responder_type": self.responder_type,
            "current_zone": self.location,
            "status": self.get_status(),
        }

    def __repr__(self):
        return (
            f"{self.responder_type}({self.responder_id}, {self.location}, "
            f"{self._status})"
        )


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


class Rescue(Responder):
    responder_type = "Rescue"

    def describe_duties(self):
        return "Performs search and rescue operations."


class Hazmat(Responder):
    responder_type = "Hazmat"

    def describe_duties(self):
        return "Handles hazardous material incidents."


RESPONDER_TYPES = {
    "Ambulance": Ambulance,
    "FireTruck": FireTruck,
    "Police": Police,
    "Rescue": Rescue,
    "Hazmat": Hazmat,
}
