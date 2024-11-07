CREATE TABLE system_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cpu FLOAT,
    memory FLOAT,
    disk FLOAT,
    disk_read FLOAT,
    disk_write FLOAT,
    network_receive FLOAT,
    network_transmit FLOAT,
    cpu_temp FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE TABLE latencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_name VARCHAR(255),
    response_time FLOAT,  -- Time in ms, or 0 if ping fails
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);