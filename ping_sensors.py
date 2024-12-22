import json
import mysql.connector
import math
from ping3 import ping
from datetime import datetime, timedelta

# Load configuration from the JSON file
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# General function to connect to the MySQL database
def connect_db(database):
    config = load_config()  # Load the configuration
    db_config = config['databases'][database]  # Get the database configuration

    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config.get('charset', 'utf8mb4'),  # Default charset if not provided
        collation=db_config.get('collation', 'utf8mb4_unicode_ci')  # Default collation if not provided
    )
    return connection

# Save ping result to the system_monitoring database 
def save_ping_to_db(sensor_name, response_time):
    connection = connect_db('system_monitoring')  # Connect to the system_monitoring DB
    cursor = connection.cursor()

    # Insert data into the latencies table
    cursor.execute("""
        INSERT INTO latencies (sensor_name, response_time)
        VALUES (%s, %s)
    """, (sensor_name, response_time))

    connection.commit()
    cursor.close()
    connection.close()

# Insert alert into the whatsapp database
def insert_alert(phone, message):
    connection = connect_db('whatsapp')  # Connect to the WhatsApp DB
    cursor = connection.cursor()

    # Get the current date and time
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M Hs')

    # Load the config to get node info
    config = load_config()
    node = config.get('node', 'Unknown Node')

    # Modify the message to include the node and timestamp
    message_with_timestamp_and_node = f"*[{node}]* {message} \nDate: {current_datetime}"

    # Insert alert into the alerts table
    cursor.execute("""
        INSERT INTO messages (phone, message)
        VALUES (%s, %s)
    """, (phone, message_with_timestamp_and_node))

    connection.commit()
    cursor.close()
    connection.close()

# Function to clean old pings from the database (older than 30 days)
def clean_old_pings():
    connection = connect_db('system_monitoring')  # Connect to the system_monitoring DB
    cursor = connection.cursor()

    # Calculate the cutoff date (30 days ago)
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    # Delete records older than the cutoff date
    cursor.execute("""
        DELETE FROM latencies
        WHERE timestamp < %s
    """, (cutoff_timestamp,))

    connection.commit()
    cursor.close()
    connection.close()

# Function to ping a sensor and return the result
def ping_sensor(ip_address):
    try:
        # Perform the ping using ping3
        response_time = ping(ip_address)
        
        # If the response_time is None, it means the ping failed, return 0
        if response_time is None:
            return 0
        
        # Truncate the response time to two decimal places
        return math.trunc(response_time * 1000)
    except Exception as e:
        # Return 0 if any error occurs (e.g., timeout or unreachable)
        return 0

# Function to check and notify if the ping exceeds the threshold or if the ping is 0
def check_ping_threshold(sensor_name, response_time, threshold):
    config = load_config()
    node = config.get('node', 'Unknown Node')  # Get the node name for context

    if response_time == 0:
        # If ping is 0, send an alert saying the node is offline
        for phone in config['notifications']:
            message = f"ALERT: {sensor_name} did not respond!"
            insert_alert(phone, message)
        print(f"ALERT: {sensor_name} did not respond!")
    elif response_time > threshold:
        # If ping exceeds threshold, send an alert
        for phone in config['notifications']:
            message = f"ALERT: {sensor_name} ping is too high! \nResponse time: {response_time} ms"
            insert_alert(phone, message)
        print(f"ALERT: {sensor_name} ping is too high. Response time: {response_time} ms")

# Function to collect ping data for all sensors
def collect_and_save_ping_data():
    config = load_config()  # Load the configuration
    sensors = config['sensors']  # Get the list of sensors

    # Clean old pings before collecting new data
    clean_old_pings()

    for sensor in sensors:
        response_time = ping_sensor(sensor['ip'])
        
        # Simplified output for online/offline status with color
        if response_time == 0:
            print(f"Pinging {sensor['name']} ..... \033[31mOFFLINE\033[0m")  # Red for OFFLINE
        else:
            print(f"Pinging {sensor['name']} ..... \033[32mONLINE {response_time}ms\033[0m")  # Green for ONLINE

        # Save the ping result to the system_monitoring database
        save_ping_to_db(sensor['name'], response_time)

        # Check if the ping exceeds the threshold or is 0, and send an alert if needed
        check_ping_threshold(sensor['name'], response_time, sensor['threshold'])

# Main function to run the ping process
if __name__ == "__main__":
    collect_and_save_ping_data()
