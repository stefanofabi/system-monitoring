import json
import mysql.connector
from ping3 import ping
from datetime import datetime, timedelta

# Load configuration from the JSON file
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# Connect to the MySQL database
def connect_db():
    config = load_config()  # Load the configuration
    db_config = config['database']  # Get database-specific config
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset'],
        collation=db_config['collation']
    )
    return connection

# Save ping result to the database (without 'ip_address' column)
def save_ping_to_db(sensor_name, response_time):
    connection = connect_db()
    cursor = connection.cursor()

    # Insert data into the ping table without the 'ip_address' column
    cursor.execute("""
        INSERT INTO latencies (sensor_name, response_time)
        VALUES (%s, %s)
    """, (sensor_name, response_time))

    connection.commit()
    cursor.close()
    connection.close()

# Function to clean old pings from the database (older than 30 days)
def clean_old_pings():
    connection = connect_db()
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
        return response_time * 1000  # Convert seconds to milliseconds
    except Exception as e:
        # Return 0 if any error occurs (e.g., timeout or unreachable)
        return 0

# Function to collect ping data for all sensors
def collect_and_save_ping_data():
    config = load_config()  # Load the configuration
    sensors = config['sensors']  # Get the list of sensors

    # Clean old pings before collecting new data
    clean_old_pings()

    for sensor in sensors:
        print(f"Pinging {sensor['name']} (IP: {sensor['ip']})")
        
        # Ping the sensor and get the result
        response_time = ping_sensor(sensor['ip'])
        
        # Display the result
        if response_time == 0:
            print(f"  {sensor['name']} is offline or unreachable. Ping value: 0 ms")
        else:
            print(f"  {sensor['name']} is online. Response time: {response_time} ms")

        # Save the ping result to the database (only store response_time)
        save_ping_to_db(sensor['name'], response_time)

# Main function to run the ping process
if __name__ == "__main__":
    collect_and_save_ping_data()