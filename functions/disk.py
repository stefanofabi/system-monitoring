import psutil
import time

def get_disk_usage():
    disk = psutil.disk_usage('/')
    disk_used_percentage = disk.percent  # Get the percentage of disk used directly from psutil
    return disk_used_percentage

def get_disk_io():
    previous_disk = psutil.disk_io_counters()
    time.sleep(1)
    current_disk = psutil.disk_io_counters()
    disk_read = (current_disk.read_bytes - previous_disk.read_bytes) / (1024**2)  # Convert to MB/s
    disk_write = (current_disk.write_bytes - previous_disk.write_bytes) / (1024**2)  # Convert to MB/s
    return disk_read, disk_write

# Function to get disk IO wait time
def get_disk_wait():
    cpu_times = psutil.cpu_times_percent(interval=1)
    return cpu_times.iowait