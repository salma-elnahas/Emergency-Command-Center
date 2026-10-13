from queue import Queue
from incident import Incident , InvalidIncidentException
from datetime import datetime, timedelta
import re


class IncidentManager:
    # Can be used for text purposes
    SEVERITY_LEVELS = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "low"}
    
    def __init__(self):
        self.incidents = Queue()
    
    def add_incident(self,incident):
        self.incidents.enqueue(incident)
      
    def remove_incident(self):
        return self.incidents.dequeue() 
    
    @staticmethod     
    def id_number(incident_id):
        if not isinstance(incident_id, str) or not re.match(r'^INC\d{4}$', incident_id):
            raise InvalidIncidentException("Invalid ID format! Must be in format INCXXXX.")
        # Extract the numeric part after 'INC' and convert to int
        return int(incident_id[3:])
    def find_by_id(self,id):
        if id is None:
            return None
        # Using binary search because ids are generated in increasing order
        id_number = IncidentManager.id_number(id)
        items = self.incidents.queue
        low, high = 0, len(items) - 1
        while low <= high:
            mid = (low + high) // 2
            mid_number = IncidentManager.id_number(items[mid].get_id())
            
            if mid_number == id_number:
                return items[mid]
            elif mid_number < id_number:
                low = mid + 1
            else:
                high = mid - 1
        return None
                
    def find_by_location(self, location):
        # Find incidents in a given location using sequential search
        location = location.strip().lower()
        results = []
        for inc in self.incidents.queue:
            if location in inc.get_location().lower():
                results.append(inc)
        return results
    
    
    
# def main():
#     manager = IncidentManager()  
    
#     print("=== 1. TESTING VALID INCIDENT CREATION ===")
#     try:
#         # Severity argument removed from constructor call
#         valid_incident = Incident(
#             type="infrastructure failure", 
#             description="Kitchen fire on the second floor", 
#             time=datetime.now(), 
#             location="Cairo", 
#             reporter_name="Ahmed", 
#             reporter_phone="01012345678"
#         )  
#         manager.add_incident(valid_incident)  
#         print("Successfully created and added:", valid_incident)  
#     except InvalidIncidentException as e:
#         print("Unexpected error on valid input:", e)  

#     print("\n=== 2. TESTING INVALID INPUTS (Should raise exception & not consume ID) ===")
    
#     # Test Invalid Type (Non-string) - Argument list updated (no severity argument)
#     try:
#         Incident(123, "Kitchen fire on the second floor", datetime.now(), "Cairo", "Ali", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Type (not str):", e)  

#     # Test Invalid Type (Not in allowed list)
#     try:
#         Incident("alien attack", "Kitchen fire on the second floor", datetime.now(), "Cairo", "Ali", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Type (unsupported):", e)  

#     # Test Invalid Description (Too short)
#     try:
#         Incident("fire", "Bad", datetime.now(), "Cairo", "Ali", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Description (too short):", e)  

#     # Test Invalid Time (In the future)
#     try:
#         future_time = datetime.now() + timedelta(days=1)
#         Incident("fire", "Kitchen fire on the second floor", future_time, "Cairo", "Ali", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Time (future):", e)  

#     # Test Invalid Location (Too short)
#     try:
#         Incident("fire", "Kitchen fire on the second floor", datetime.now(), "C", "Ali", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Location (too short):", e)  

#     # Test Invalid Reporter Name (Too short)
#     try:
#         Incident("fire", "Kitchen fire on the second floor", datetime.now(), "Cairo", "A", "01012345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Reporter Name (too short):", e)  

#     # Test Invalid Phone Format (Wrong length)
#     try:
#         Incident("fire", "Kitchen fire on the second floor", datetime.now(), "Cairo", "Ali", "0101234")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Phone Format (too short):", e)  

#     # Test Invalid Phone Format (Wrong prefix)
#     try:
#         Incident("fire", "Kitchen fire on the second floor", datetime.now(), "Cairo", "Ali", "09912345678")  
#     except InvalidIncidentException as e:
#         print("Caught Invalid Phone Format (wrong prefix):", e)  

#     print(f"\nFinal ID Counter Check (Should only have incremented once): INC{Incident.id_counter:04d}")  
#     print("\n=== 3. TESTING ID REGEX & SEARCH LOOKUPS ===")
#     # Test valid ID lookup
#     found = manager.find_by_id("INC0001")
#     print("Found by valid ID (INC0001):", found)

#     # Test invalid ID regex format lookup (e.g., missing numbers or wrong prefix)
#     try:
#         manager.find_by_id("INVALID_ID")
#     except InvalidIncidentException as e:
#         print(e)
        
# main()