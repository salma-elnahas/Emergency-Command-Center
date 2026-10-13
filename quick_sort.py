from calculate_priority import calculate_priority
import random
from datetime import datetime
def compare_incident(a,b,now,sort_by): # -1 if a first and 1 if b first
    if sort_by == "priority":
        priority_a= calculate_priority(a,now)
        priority_b= calculate_priority(b,now)
        if priority_a > priority_b:
            return -1
        elif priority_b > priority_a:
            return 1
    elif sort_by == "severity":
        severity_a = int(a.get_severity())
        severity_b = int(b.get_severity())

        if severity_a > severity_b:
            return -1
        elif severity_a < severity_b:
            return 1
    time_a=a.get_time()
    time_b=b.get_time()
    if time_a < time_b:
        return -1
    elif time_a > time_b:
        return 1
    id_a=str(a.get_id()).strip()
    id_b=str(b.get_id()).strip()
    if id_a<id_b:
        return -1
    elif id_a>id_b:
        return 1
    return 0

def partition(incidents, low, high, now, stats, sort_by):
    pivot_i=random.randint(low,high)
    if pivot_i!=high:
        incidents[pivot_i],incidents[high]=incidents[high],incidents[pivot_i]
        stats["swaps"] += 1
    pivot=incidents[high]
    i=low-1
    for j in range(low,high):
        stats["comparisons"] += 1
        if compare_incident(incidents[j],pivot,now,sort_by)<=0:
            i+=1
            if i != j:
                incidents[i],incidents[j]=incidents[j],incidents[i]
                stats["swaps"] += 1
    if i+1 != high:
        incidents[i+1],incidents[high]=incidents[high],incidents[i+1]
        stats["swaps"] += 1
    return i+1

def quick_sort(incidents, low, high, now, stats,sort_by):
    stats["recursive_calls"] += 1
    if low < high:
        pivot=partition(incidents, low, high, now, stats,sort_by)
        quick_sort(incidents, low, pivot-1, now, stats,sort_by)
        quick_sort(incidents, pivot+1, high, now, stats,sort_by)

def random_quick_sort(incidents, now=None, sort_by="priority"):
    if sort_by not in ("priority", "severity", "timestamp"):
        raise ValueError("Sort by must be priority, severity, or timestamp.")
    sorting_incidents=incidents.copy()
    stats = {"comparisons": 0, "swaps": 0, "recursive_calls": 0}
    if len(sorting_incidents) == 0:
        return sorting_incidents,stats
    if now is None:
        time=sorting_incidents[0].get_time()
        now=datetime.now(tz=time.tzinfo)
    quick_sort(sorting_incidents, 0, len(sorting_incidents)-1, now, stats, sort_by)
    return sorting_incidents,stats

