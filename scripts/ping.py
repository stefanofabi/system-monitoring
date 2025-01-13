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
def save_ping_to_db(sensor, response_time):
    connection = connect_db('system_monitoring')  # Connect to the system_monitoring DB
    cursor = connection.cursor()

    # Insert data into the latencies table
    cursor.execute(""" 
        INSERT INTO latencies (sensor_id, response_time)
        VALUES (%s, %s)
    """, (sensor['id'], response_time))

    connection.commit()
    cursor.close()
    connection.close()

# Insert alert into the whatsapp database
def insert_alert(phone, message):
    connection = connect_db('whatsapp')  # Connect to the WhatsApp DB
    cursor = connection.cursor()

    # Insert alert into the alerts table
    cursor.execute(""" 
        INSERT INTO messages (phone, message)
        VALUES (%s, %s)
    """, (phone, message))

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

# Function to make up to 4 ping attempts and return the result
def ping_sensor(ip_address):
    max_attempts = 4  # Maximum number of attempts
    for attempt in range(max_attempts):
        # Perform the ping
        response_time = ping(ip_address, unit='ms')
            
        # If the response time is None, it means the ping failed
        if not response_time:
            if attempt == max_attempts - 1:
                # If it's the last attempt and it fails, return 0
                return 0
            else:
                # If it's not the last attempt, continue trying
                continue

        # Truncate the response time to two decimal places
        return math.trunc(response_time)

    return 0  # If all attempts fail, return 0

# Function to get the current date and time as a formatted string
def get_current_time():
    return datetime.now().strftime('%d %b %Y %H:%M Hs')

# Function to check and notify if the ping exceeds the threshold or if the ping is 0
def check_ping_threshold(sensor, response_time):
    config = load_config()
    node = config.get('node', 'Unknown Node')
    failure_threshold = config['thresholds']['failures']

    connection = connect_db('system_monitoring')  # Connect to the system_monitoring DB
    cursor = connection.cursor()

    # If the ping response time is 0 (offline)
    if response_time == 0:
        # Increment the 'failed' count in the sensor object
        sensor['failed'] += 1

        # Send an alert that the sensor is not responding
        message = f"⚠️ *{sensor['name']} not responding* ⚠️ \n\n*Node:* {node} \n*Date:* {get_current_time()}"
        insert_alert(config['ping-alerts-channel'], message)
        print(f"[{get_current_time()}] - {sensor['name']} not responding on {node}")

        # If the 'failed' count exceeds the failure threshold, deactivate the sensor
        if sensor['failed'] >= failure_threshold:
            cursor.execute("""
                UPDATE sensors
                SET failed = %s, active = FALSE
                WHERE id = %s
            """, (sensor['failed'], sensor['id'],))

            message = f"[{get_current_time()}] - {sensor['name']} has been deactivated due to multiple failures"
            insert_alert(config['ping-alerts-channel'], message)

            print(f"\033[31m[{get_current_time()}] - {sensor['name']} has been deactivated due to multiple failures\033[0m")
        else: 
            cursor.execute("""
                UPDATE sensors
                SET failed = %s
                WHERE id = %s
            """, (sensor['failed'], sensor['id'],))
    else:
        # If the ping is successful (response time > 0), reset 'failed' count to 0
        sensor['failed'] = 0
        
        # If ping exceeds threshold, send an alert
        if response_time > sensor['threshold']:
            if sensor['high_ping_count'] > 5:
                sensor['high_ping_count'] = 0

                message = f"⚠️ *{sensor['name']} ping is high* ⚠️ \n\n*Node:* {node} \n*Response time:* {response_time} ms \n*Date:* {get_current_time()}"
                insert_alert(config['ping-alerts-channel'], message)

                print(f"[{get_current_time()}] - {sensor['name']} ping is high on {node}. Response time: {response_time} ms")
            
                cursor.execute("""
                    UPDATE sensors
                    SET high_ping_count = %s, failed = %s
                    WHERE id = %s
                """, (sensor['high_ping_count'], sensor['failed'], sensor['id']))
            else: 
                sensor['high_ping_count'] += 1
                
                cursor.execute("""
                    UPDATE sensors
                    SET high_ping_count = %s, failed = %s
                    WHERE id = %s
                """, (sensor['high_ping_count'], sensor['failed'], sensor['id']))

    connection.commit()  # Commit the changes
    cursor.close()
    connection.close()

# Function to collect ping data for all sensors (updated)
def collect_and_save_ping_data():
    # Get the list of active sensors from the database
    sensors = get_sensors_from_db()

    # Clean old pings before collecting new data
    clean_old_pings()

    for sensor in sensors:
        response_time = ping_sensor(sensor['ip'])
        
        # Simplified output for online/offline status with color
        if response_time == 0:
            print(f"[{get_current_time()}] Pinging {sensor['name']} ..... \033[31mOFFLINE\033[0m")  # Red for OFFLINE
        else:
            print(f"[{get_current_time()}] Pinging {sensor['name']} ..... \033[32mONLINE {response_time}ms\033[0m")  # Green for ONLINE

        # Save the ping result to the system_monitoring database
        save_ping_to_db(sensor, response_time)

        # Check if the ping exceeds the threshold or is 0, and send an alert if needed
        check_ping_threshold(sensor, response_time)

# Function to get the sensors from the database with their thresholds
def get_sensors_from_db():
    connection = connect_db('system_monitoring')  # Connect to the system_monitoring DB
    cursor = connection.cursor(dictionary=True)

    # Select all sensors from the sensors table
    cursor.execute("""
        SELECT id, name, ip, threshold, failed, high_ping_count, active
        FROM sensors
        WHERE active = TRUE
    """)
    
    sensors = cursor.fetchall()  # Fetch all the sensors
    cursor.close()
    connection.close()
    
    return sensors

# Main function to run the ping process
if __name__ == "__main__":
    collect_and_save_ping_data()
