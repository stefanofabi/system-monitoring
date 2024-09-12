import psutil
import time
import mysql.connector
import json
from datetime import datetime, timedelta

# Load database configuration from a JSON file
def load_db_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# Connect to the MySQL database
def connect_db():
    config = load_db_config()
    connection = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset=config['charset'],
        collation=config['collation']
    )
    return connection

# Clean old records from the database
def clean_old_records():
    connection = connect_db()
    cursor = connection.cursor()

    # Calculate the timestamp for 30 days ago
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    # Delete records older than the cutoff timestamp
    cursor.execute("""
        DELETE FROM system_stats
        WHERE timestamp < %s
    """, (cutoff_timestamp,))

    connection.commit()
    cursor.close()
    connection.close()

# Save system stats to the database
def save_to_db(cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp):
    connection = connect_db()
    cursor = connection.cursor()

    # Insert data into the system_stats table
    cursor.execute("""
        INSERT INTO system_stats (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp))

    connection.commit()
    cursor.close()
    connection.close()

# Functions to collect system information
def get_cpu_usage():
    cpu_total = psutil.cpu_percent(interval=1)
    return cpu_total

def get_memory():
    memory = psutil.virtual_memory()
    memory_used_percentage = memory.percent  # Get the percentage of memory used directly from psutil
    return memory_used_percentage

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

def get_network_io():
    previous_network = psutil.net_io_counters()
    time.sleep(1)
    current_network = psutil.net_io_counters()
    network_receive_mb = (current_network.bytes_recv - previous_network.bytes_recv) / (1024**2)  # Convert to MB/s
    network_transmit_mb = (current_network.bytes_sent - previous_network.bytes_sent) / (1024**2)  # Convert to MB/s

    # Convert from MB/s to Mbps
    network_receive_mbps = network_receive_mb * 8
    network_transmit_mbps = network_transmit_mb * 8
    return network_receive_mbps, network_transmit_mbps

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            # On some systems, temperatures are reported under 'coretemp'
            temp = temps['coretemp'][0].current
        elif 'cpu_thermal' in temps:
            # On some systems, temperatures are reported under 'cpu_thermal'
            temp = temps['cpu_thermal'][0].current
        else:
            temp = None
    except (AttributeError, KeyError):
        temp = None
    return temp

# Function to display and save system information
def display_and_save_info():
    cpu = get_cpu_usage()
    memory_used_percentage = get_memory()
    disk_used_percentage = get_disk_usage()
    disk_read, disk_write = get_disk_io()
    network_receive_mbps, network_transmit_mbps = get_network_io()
    cpu_temp = get_cpu_temp()

    # Display results
    print(f"Total CPU Usage: {cpu}%")
    print(f"Memory Used: {memory_used_percentage:.2f}%")
    print(f"Disk Used: {disk_used_percentage:.2f}%")
    print(f"Disk Read Speed: {disk_read:.2f} MB/s")
    print(f"Disk Write Speed: {disk_write:.2f} MB/s")
    print(f"Network Receive Speed: {network_receive_mbps:.2f} Mbps")
    print(f"Network Transmit Speed: {network_transmit_mbps:.2f} Mbps")
    print(f"CPU Temperature: {cpu_temp}°C" if cpu_temp is not None else "CPU Temperature: Not Available")

    # Save results to the database
    save_to_db(cpu, memory_used_percentage, disk_used_percentage, disk_read, disk_write, network_receive_mbps, network_transmit_mbps, cpu_temp)

# Main function
if __name__ == "__main__":
    # Clean old records before saving new ones
    clean_old_records()
    display_and_save_info()
