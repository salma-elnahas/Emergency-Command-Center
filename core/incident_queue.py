class Queue:
    def __init__(self):
        self.queue = []

    def is_empty(self):
        return len(self.queue) == 0

    def enqueue(self, element):
        self.queue.append(element)

    def dequeue(self):
        return None if self.is_empty() else self.queue.pop(0)

    def front(self):
        return None if self.is_empty() else self.queue[0]

    def size(self):
        return len(self.queue)

    def to_list(self):
        return list(self.queue)
