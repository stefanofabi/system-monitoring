import mysql.connector
import json
from datetime import datetime, timedelta
import math

from functions.cpu import get_cpu_usage, get_cpu_temp
from functions.memory import get_memory, get_swap_memory
from functions.disk import get_disk_usage, get_disk_io, get_disk_wait
from functions.network import get_network_io

def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

def connect_db(database):
    config = load_config()
    db_config = config['databases'][database]
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset'] if 'charset' in db_config else 'utf8mb4',
        collation=db_config['collation'] if 'collation' in db_config else 'utf8mb4_unicode_ci'
    )
    return connection

def clean_old_records():
    connection = connect_db('system_monitoring')
    cursor = connection.cursor()
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""DELETE FROM system_stats WHERE timestamp < %s""", (cutoff_timestamp,))
    connection.commit()
    cursor.close()
    connection.close()

def save_to_db(cpu, cpu_temp, memory, swap, disk, disk_read, disk_write, disk_wait, network_receive, network_transmit):
    latest_record = get_latest_system_stats()

    config = load_config()
    thresholds = config['thresholds']
    
    connection = connect_db('system_monitoring')
    cursor = connection.cursor()

    cpu_count = latest_record['cpu_count'] + 1 if cpu > thresholds['cpu'] else 0
    cpu_temp_count = latest_record['cpu_temp_count'] + 1 if cpu_temp > thresholds['temperature'] else 0
    memory_count = latest_record['memory_count'] + 1 if memory > thresholds['memory'] else 0
    swap_count = latest_record['swap_count'] + 1 if swap > thresholds['swap'] else 0
    disk_count = latest_record['disk_count'] + 1 if disk > thresholds['disk'] else 0
    disk_read_count = latest_record['disk_read_count'] + 1 if disk_read > thresholds['io'] else 0
    disk_write_count = latest_record['disk_write_count'] + 1 if disk_write > thresholds['io'] else 0
    disk_wait_count = latest_record['disk_wait_count'] + 1 if disk_wait > thresholds['iowait'] else 0
    network_receive_count = latest_record['network_receive_count'] + 1 if network_receive > thresholds['network'] else 0
    network_transmit_count = latest_record['network_transmit_count'] + 1 if network_transmit > thresholds['network'] else 0

    cursor.execute(""" 
        INSERT INTO system_stats (
            cpu, cpu_temp, memory, swap, disk, disk_read, disk_write, network_receive, 
            network_transmit, disk_wait, 
            cpu_count, cpu_temp_count, memory_count, swap_count, disk_count, 
            disk_read_count, disk_write_count, disk_wait_count, 
            network_receive_count, network_transmit_count
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        cpu, cpu_temp, 
        memory, swap, 
        disk, disk_read, disk_write, 
        network_receive, network_transmit, disk_wait,
        cpu_count, cpu_temp_count, memory_count, swap_count, disk_count, 
        disk_read_count, disk_write_count, disk_wait_count, 
        network_receive_count, network_transmit_count
    ))

    connection.commit()
    cursor.close()
    connection.close()

def insert_alert(phone, message):
    connection = connect_db('whatsapp')
    cursor = connection.cursor()
    current_datetime = get_current_time()
    config = load_config()
    node = config.get('node', 'Unknown Node') 
    message_with_timestamp_and_node = f"⚠️ *Resource threshold reached* ⚠️ \n\n*Node:* {node} \n*Date:* {current_datetime} \n\n{message}"
    cursor.execute("""
        INSERT INTO messages (phone, message)
        VALUES (%s, %s)
    """, (phone, message_with_timestamp_and_node))
    connection.commit()
    cursor.close()
    connection.close()

def check_thresholds(cpu, cpu_temp, memory_used_percentage, swap_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps):
    config = load_config()
    thresholds = config['thresholds']
    alert_message = ""
    latest_record = get_latest_system_stats()

    def check_and_alert(resource_name, value, threshold, count, count_threshold, unit=""):
        if value > threshold and count > count_threshold:
            return f"{resource_name} usage is {value}{unit}\n"
        return ""
    
    alert_message += check_and_alert("CPU", cpu, thresholds['cpu'], latest_record['cpu_count'], 5, "%")
    alert_message += check_and_alert("CPU Temperature", cpu_temp, thresholds['temperature'], latest_record['cpu_temp_count'], 5, "ºC")
    alert_message += check_and_alert("Memory", memory_used_percentage, thresholds['memory'], latest_record['memory_count'], 5, "%")
    alert_message += check_and_alert("Swap", swap_used_percentage, thresholds['swap'], latest_record['swap_count'], 5, "%")
    alert_message += check_and_alert("Disk", disk_used_percentage, thresholds['disk'], latest_record['disk_count'], 5, "%")
    alert_message += check_and_alert("Disk Read", disk_read, thresholds['io'], latest_record['disk_read_count'], 5, " MB/s")
    alert_message += check_and_alert("Disk Write", disk_write, thresholds['io'], latest_record['disk_write_count'], 5, " MB/s")
    alert_message += check_and_alert("Disk Wait", disk_wait, thresholds['iowait'], latest_record['disk_wait_count'], 5, " ms")
    alert_message += check_and_alert("Network Receive", network_receive_mbps, thresholds['network'], latest_record['network_receive_count'], 5, " Mbps")
    alert_message += check_and_alert("Network Transmit", network_transmit_mbps, thresholds['network'], latest_record['network_transmit_count'], 5, " Mbps")

    if alert_message:
        alert_message = alert_message.strip()
        insert_alert(config['resources-alerts-channel'], alert_message)

def get_latest_system_stats():
    connection = connect_db('system_monitoring')
    cursor = connection.cursor(dictionary=True) 
    query = """
        SELECT *
        FROM system_stats
        ORDER BY timestamp DESC
        LIMIT 1
    """
    cursor.execute(query)  
    result = cursor.fetchone() 
    cursor.close()
    connection.close()

    if result:
        return result  
    else:
        return {
            'id': None,
            'cpu': 0.0,
            'cpu_temp': 0.0,
            'memory': 0.0,
            'swap': 0.0,
            'disk': 0.0,
            'disk_read': 0.0,
            'disk_write': 0.0,
            'disk_wait': 0.0,
            'network_receive': 0.0,
            'network_transmit': 0.0,
            'cpu_count': 0,
            'cpu_temp_count': 0,
            'memory_count': 0,
            'swap_count': 0,
            'disk_count': 0,
            'disk_read_count': 0,
            'disk_write_count': 0,
            'disk_wait_count': 0,
            'network_receive_count': 0,
            'network_transmit_count': 0,
            'timestamp': None,
        }

def get_current_time():
    return datetime.now().strftime('%d %b %Y %H:%M Hs')

def display_and_save_info():
    config = load_config()
    thresholds = config["thresholds"]
    
    cpu = get_cpu_usage()
    cpu_temp = get_cpu_temp()
    memory_used_percentage = get_memory()
    swap_used_percentage = get_swap_memory()
    disk_used_percentage = get_disk_usage()
    disk_read, disk_write = get_disk_io()
    disk_wait = get_disk_wait()
    network_receive_mbps, network_transmit_mbps = get_network_io()

    cpu = math.trunc(cpu)
    cpu_temp = math.trunc(cpu_temp) if cpu_temp is not None else None
    memory_used_percentage = math.trunc(memory_used_percentage)
    swap_used_percentage = math.trunc(swap_used_percentage)
    disk_used_percentage = math.trunc(disk_used_percentage)
    disk_read = math.trunc(disk_read)
    disk_write = math.trunc(disk_write)
    disk_wait = math.trunc(disk_wait)
    network_receive_mbps = math.trunc(network_receive_mbps)
    network_transmit_mbps = math.trunc(network_transmit_mbps)
    
    def print_with_color(message, is_above_threshold):
        color_code = "\033[31m" if is_above_threshold else "\033[32m"
        print(f"{color_code}{message}\033[0m")

    print_with_color(f"CPU: {cpu}%", cpu > thresholds["cpu"])
    print_with_color(f"CPU Temperature: {cpu_temp}°C" if cpu_temp is not None else "CPU Temperature: Not Available", cpu_temp > thresholds["temperature"] if cpu_temp is not None else False)
    print_with_color(f"Memory: {memory_used_percentage}%", memory_used_percentage > thresholds["memory"])
    print_with_color(f"Swap: {swap_used_percentage}%", swap_used_percentage > thresholds["swap"])
    print_with_color(f"Disk: {disk_used_percentage}%", disk_used_percentage > thresholds["disk"])
    print_with_color(f"Disk Read: {disk_read} MB/s", disk_read > thresholds["io"])
    print_with_color(f"Disk Write: {disk_write} MB/s", disk_write > thresholds["io"])
    print_with_color(f"Disk IO Wait: {disk_wait}%", disk_wait > thresholds["iowait"])
    print_with_color(f"Network Receive: {network_receive_mbps} Mbps", network_receive_mbps > thresholds["network"])
    print_with_color(f"Network Transmit: {network_transmit_mbps} Mbps", network_transmit_mbps > thresholds["network"])

    save_to_db(cpu, cpu_temp, memory_used_percentage, swap_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps)
    check_thresholds(cpu, cpu_temp, memory_used_percentage, swap_used_percentage, disk_used_percentage, disk_read, disk_write, disk_wait, network_receive_mbps, network_transmit_mbps)

if __name__ == "__main__":
    clean_old_records()
    display_and_save_info()
