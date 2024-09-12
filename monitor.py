import psutil
import time
import mysql.connector
import json

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

# Save system stats to the database
def save_to_db(cpu_percentage, cpu_total, memory_total, memory_used, memory_available, disk_read, disk_write, network_receive_mbps, network_transmit_mbps):
    connection = connect_db()
    cursor = connection.cursor()

    # Convert the list of CPU percentages to a JSON string
    cpu_percentage_json = json.dumps(cpu_percentage)

    # Insert data into the system_stats table
    cursor.execute("""
        INSERT INTO system_stats (cpu_percentage, cpu_total, memory_total, memory_used, memory_available, disk_read, disk_write, network_receive_mbps, network_transmit_mbps)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (cpu_percentage_json, cpu_total, memory_total, memory_used, memory_available, disk_read, disk_write, network_receive_mbps, network_transmit_mbps))

    connection.commit()
    cursor.close()
    connection.close()

# Functions to collect system information
def get_cpu_usage():
    cpu_percentage = psutil.cpu_percent(interval=1, percpu=True)
    cpu_total = psutil.cpu_percent(interval=1) 
    return cpu_percentage, cpu_total

def get_memory():
    memory = psutil.virtual_memory()
    total_mb = memory.total / (1024 ** 2)
    used_mb = memory.used / (1024 ** 2)
    available_mb = memory.available / (1024 ** 2)
    return total_mb, used_mb, available_mb

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

# Function to display and save system information
def display_and_save_info():
    cpu_percentage, cpu_total = get_cpu_usage()
    memory_total, memory_used, memory_available = get_memory()
    disk_read, disk_write = get_disk_io()
    network_receive_mbps, network_transmit_mbps = get_network_io()

    # Display results
    print(f"CPU Usage by Core: {cpu_percentage}")
    print(f"Total CPU Usage: {cpu_total}%")
    print(f"Total Memory: {memory_total:.0f} MB")
    print(f"Used Memory: {memory_used:.0f} MB")
    print(f"Available Memory: {memory_available:.0f} MB")
    print(f"Disk Read Speed: {disk_read:.2f} MB/s")
    print(f"Disk Write Speed: {disk_write:.2f} MB/s")
    print(f"Network Receive Speed: {network_receive_mbps:.2f} Mbps")
    print(f"Network Transmit Speed: {network_transmit_mbps:.2f} Mbps")

    # Save results to the database
    save_to_db(cpu_percentage, cpu_total, memory_total, memory_used, memory_available, disk_read, disk_write, network_receive_mbps, network_transmit_mbps)

# Main function
if __name__ == "__main__":
    display_and_save_info()
