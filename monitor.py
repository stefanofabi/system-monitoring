import psutil
import time
import mysql.connector
import json
from datetime import datetime, timedelta
import math

# Load database configuration from a JSON file
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# Connect to the MySQL database
def connect_db(database):
    config = load_config()
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
def save_to_db(cpu, memory, disk, disk_read, disk_write, disk_wait, network_receive, network_transmit, cpu_temp):
    connection = connect_db('system_monitoring')
    cursor = connection.cursor()

    # Insert data into the system_stats table, including disk_wait
    cursor.execute("""
        INSERT INTO system_stats (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp, disk_wait)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (cpu, memory, disk, disk_read, disk_write, network_receive, network_transmit, cpu_temp, disk_wait))

    connection.commit()
    cursor.close()
    connection.close()

# Insert alert into the whatsapp database
def insert_alert(phone, message):
    connection = connect_db('whatsapp')
    cursor = connection.cursor()

    current_datetime = get_current_time()

    config = load_config()
    node = config.get('node', 'Unknown Node') 
    
    message_with_timestamp_and_node = f"⚠️ *Resource threshold reached* ⚠️ \n\n*Node:* {node} \n*Date:* {current_datetime} \n\n{message}"
    
    # Insert alert into the alerts table
    cursor.execute("""
        INSERT INTO messages (phone, message)
        VALUES (%s, %s)
    """, (phone, message_with_timestamp_and_node))
    
    connection.commit()
    cursor.close()
    connection.close()

def check_thresholds(cpu, cpu_temp, memory_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps):
    # Load the configuration and thresholds from the database
    config = load_config()
    thresholds = config['thresholds']
    
    # Variable to store the concatenated alert messages
    alert_message = ""

    # Check CPU usage
    if cpu > thresholds['cpu']:
        alert_message += f"CPU usage is {cpu}%\n"
    
    # Check CPU temperature
    if cpu_temp > thresholds['temperature']:
        alert_message += f"CPU TEMPERATURE usage is {cpu_temp}ºC\n"
    
    # Check memory usage
    if memory_used_percentage > thresholds['memory']:
        alert_message += f"Memory usage is {memory_used_percentage}%\n"
    
    # Check disk usage
    if disk_used_percentage > thresholds['disk']:
        alert_message += f"Disk usage is {disk_used_percentage}%\n"
    
    # Check disk read rate
    if disk_read > thresholds['io']:
        alert_message += f"Disk read usage is {disk_read} MB/s\n"
    
    # Check disk write rate
    if disk_write > thresholds['io']:
        alert_message += f"Disk write usage is {disk_write} MB/s\n"

    # Check disk write rate
    if disk_wait > thresholds['iowait']:
        alert_message += f"Disk wait is {disk_wait} ms\n"
    
    # Check network receive rate
    if network_receive_mbps > thresholds['network']:
        alert_message += f"Network receive usage is {network_receive_mbps} Mbps\n"

    # Check network transmit rate
    if network_transmit_mbps > thresholds['network']:
        alert_message += f"Network transmit usage is {network_transmit_mbps} Mbps\n"

    # If there are any alert messages, send and print them
    if alert_message:
        # Remove the last unnecessary newline character
        alert_message = alert_message.strip()
        
        # Send the alert message
        insert_alert(config['resources-alerts-channel'], alert_message)

# Function to get the current date and time as a formatted string
def get_current_time():
    return datetime.now().strftime('%d %b %Y %H:%M Hs')

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

# Function to get disk IO wait time
def get_disk_wait():
    cpu_times = psutil.cpu_times_percent(interval=1)
    return cpu_times.iowait

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

def display_and_save_info():
    # Load thresholds from config.json
    config = load_config()
    thresholds = config["thresholds"]
    
    cpu = get_cpu_usage()
    cpu_temp = get_cpu_temp()
    memory_used_percentage = get_memory()
    disk_used_percentage = get_disk_usage()
    disk_read, disk_write = get_disk_io()
    disk_wait = get_disk_wait()
    network_receive_mbps, network_transmit_mbps = get_network_io()

    # Truncate all the parameters before passing to save_to_db and check_thresholds
    cpu = math.trunc(cpu)
    cpu_temp = math.trunc(cpu_temp) if cpu_temp is not None else None
    memory_used_percentage = math.trunc(memory_used_percentage)
    disk_used_percentage = math.trunc(disk_used_percentage)
    disk_read = math.trunc(disk_read)
    disk_write = math.trunc(disk_write)
    disk_wait = math.trunc(disk_wait)
    network_receive_mbps = math.trunc(network_receive_mbps)
    network_transmit_mbps = math.trunc(network_transmit_mbps)
    
    # Function to print with color
    def print_with_color(message, is_above_threshold):
        color_code = "\033[31m" if is_above_threshold else "\033[32m"  # Red or green
        print(f"{color_code}{message}\033[0m")

    # Display results with color based on thresholds
    print_with_color(f"Total CPU Usage: {cpu}%", cpu > thresholds["cpu"])
    print_with_color(f"CPU Temperature: {cpu_temp}°C" if cpu_temp is not None else "CPU Temperature: Not Available", cpu_temp > thresholds["temperature"] if cpu_temp is not None else False)
    print_with_color(f"Memory Used: {memory_used_percentage}%", memory_used_percentage > thresholds["memory"])
    print_with_color(f"Disk Used: {disk_used_percentage}%", disk_used_percentage > thresholds["disk"])
    print_with_color(f"Disk Read Speed: {disk_read} MB/s", disk_read > thresholds["io"])
    print_with_color(f"Disk Write Speed: {disk_write} MB/s", disk_write > thresholds["io"])
    print_with_color(f"Disk IO Wait: {disk_wait}%", disk_wait > thresholds["iowait"])
    print_with_color(f"Network Receive Speed: {network_receive_mbps} Mbps", network_receive_mbps > thresholds["network"])
    print_with_color(f"Network Transmit Speed: {network_transmit_mbps} Mbps", network_transmit_mbps > thresholds["network"])

    # Save results to the database
    save_to_db(cpu, memory_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps, cpu_temp)
    
    # Check thresholds and insert alerts if needed
    check_thresholds(cpu, cpu_temp, memory_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps)

# Main function
if __name__ == "__main__":
    # Clean old records before saving new ones
    clean_old_records()
    display_and_save_info()
