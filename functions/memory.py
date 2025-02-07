import psutil

def get_memory():
    memory = psutil.virtual_memory()
    memory_used_percentage = memory.percent
    return memory_used_percentage

def get_swap_memory():
    swap = psutil.swap_memory()
    swap_used_percentage = (swap.used / swap.total) * 100 
    return swap_used_percentage