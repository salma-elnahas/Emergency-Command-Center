class Queue:
    def __init__(self):
        self.queue = []
        
    def is_empty(self):
        return len(self.queue) == 0
    # Add it to the back
    def enqueue(self,element):
        self.queue.append(element)     
    # Remove and return incident at the front      
    def dequeue(self):
        return None if self.is_empty() else self.queue.pop(0)       
    # Return the front incident without removing it
    def front(self):
        return None if self.is_empty() else self.queue[0]
    def size(self): 
        return len(self.queue)
    

    