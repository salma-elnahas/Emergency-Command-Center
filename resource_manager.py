
from responders import Ambulance, FireTruck, Police


class CustomHashTable:
    def __init__(self, size=10):
        self.size = size
        self.storage = [[] for _ in range(size)]

    def hash_function(self, key):
        total = 0

        for character in key:
            total += ord(character)

        return total % self.size

    def insert(self, key, value):
        index = self.hash_function(key)
        bucket = self.storage[index]

        for i in range(len(bucket)):
            if bucket[i][0] == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))

    def search(self, key):
        index = self.hash_function(key)
        bucket = self.storage[index]

        for stored_key, value in bucket:
            if stored_key == key:
                return value

        return None

    def delete(self, key):
        index = self.hash_function(key)
        bucket = self.storage[index]

        for i in range(len(bucket)):
            if bucket[i][0] == key:
                bucket.pop(i)
                return True

        return False


def binary_search(responders, target_id):
    low = 0
    high = len(responders) - 1

    while low <= high:
        mid = (low + high) // 2
        current_id = responders[mid].responder_id

        if current_id == target_id:
            return responders[mid]
        elif current_id < target_id:
            low = mid + 1
        else:
            high = mid - 1

    return None


class ResourceManager:
    def __init__(self):
        self.responders = []
        self.responder_table = CustomHashTable()

    def add_responder(self, responder):
        if self.responder_table.search(responder.responder_id):
            return False

        self.responders.append(responder)
        self.responder_table.insert(
            responder.responder_id, responder
        )

        return True

    def find_by_id(self, responder_id):
        return self.responder_table.search(responder_id)

    def find_by_binary_search(self, responder_id):
        sorted_responders = sorted(
            self.responders,
            key=lambda responder: responder.responder_id
        )

        return binary_search(sorted_responders, responder_id)

    def filter_responders(self, responder_type="All",
                          availability="All"):
        results = []

        for responder in self.responders:
            type_matches = (
                responder_type == "All"
                or responder.responder_type == responder_type
            )

            if availability == "All":
                status_matches = True
            elif availability == "Available":
                status_matches = responder.available
            else:
                status_matches = not responder.available

            if type_matches and status_matches:
                results.append(responder)

        return results

    def update_availability(self, responder_id, available):
        responder = self.find_by_id(responder_id)

        if responder is None:
            return False

        responder.available = available
        return True

    def remove_responder(self, responder_id):
        responder = self.find_by_id(responder_id)

        if responder is None:
            return False

        self.responders.remove(responder)
        self.responder_table.delete(responder_id)

        return True
