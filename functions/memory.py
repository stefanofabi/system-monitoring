import psutil

def get_memory():
    memory = psutil.virtual_memory()
    memory_used_percentage = memory.percent  # Get the percentage of memory used directly from psutil
    return memory_used_percentage