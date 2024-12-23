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
def connect_db(database):
    config = load_db_config()
    db_config = config['databases'][database]
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset'] if 'charset' in db_config else 'utf8mb4',  # Default charset
        collation=db_config['collation'] if 'collation' in db_config else 'utf8mb4_unicode_ci'  # Default collation
    )
    return connection

# Clean old records from the database
def clean_old_records():
    connection = connect_db('system_monitoring')
    cursor = connection.cursor()

    # Calculate the timestamp for 30 days ago
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    # Delete records older than the cutoff timestamp
    cursor.execute("""DELETE FROM system_stats WHERE timestamp < %s""", (cutoff_timestamp,))
    
    connection.commit()
    cursor.close()
    connection.close()

# Save system stats to the system_monitoring database
def save_to_db(cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp):
    connection = connect_db('system_monitoring')
    cursor = connection.cursor()

    # Insert data into the system_stats table
    cursor.execute("""
        INSERT INTO system_stats (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp))

    connection.commit()
    cursor.close()
    connection.close()

# Insert alert into the whatsapp database
def insert_alert(phone, message):
    connection = connect_db('whatsapp')
    cursor = connection.cursor()

    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    config = load_db_config()
    node = config.get('node', 'Unknown Node') 
    
    message_with_timestamp_and_node = f"[{node}] {message} (Date: {current_datetime})"
    
    # Insert alert into the alerts table
    cursor.execute("""
        INSERT INTO alerts (phone, message)
        VALUES (%s, %s)
    """, (phone, message_with_timestamp_and_node))
    
    connection.commit()
    cursor.close()
    connection.close()

# Check thresholds and insert alerts if needed
def check_thresholds(cpu, cpu_temp, memory, disk, network):
    config = load_db_config()
    thresholds = config['thresholds']
    
    # List to store alert messages
    alert_messages = []

    # Check CPU usage
    if cpu > thresholds['cpu']:
        alert_messages.append(f"CPU usage is {cpu}% (Threshold: {thresholds['cpu']}%)")
    
    if cpu_temp > thresholds['temperature']:
        alert_messages.append(f"CPU TEMPERATURE usage is {cpu_temp}% (Threshold: {thresholds['temperature']}ºC)")
    
    # Check Memory usage
    if memory > thresholds['memory']:
        alert_messages.append(f"Memory usage is {memory}% (Threshold: {thresholds['memory']}%)")
    
    # Check Disk usage
    if disk > thresholds['disk']:
        alert_messages.append(f"Disk usage is {disk}% (Threshold: {thresholds['disk']}%)")
    
    # Check Network usage
    if network > thresholds['network']:
        alert_messages.append(f"Network usage is {network} Mbps (Threshold: {thresholds['network']} Mbps)")

    # If there are any alert messages, print and send them
    if alert_messages:
        # Print the alert messages to the console
        for message in alert_messages:
            print(message)

        # Insert the messages into the database for all phones
        for message in alert_messages:
            insert_alert(config['resources-alerts-channel'], message)

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
    
    # Check thresholds and insert alerts if needed
    check_thresholds(cpu, cpu_temp, memory_used_percentage, disk_used_percentage, network_receive_mbps)

# Main function
if __name__ == "__main__":
    # Clean old records before saving new ones
    clean_old_records()
    display_and_save_info()
