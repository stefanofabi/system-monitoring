CREATE DATABASE system_monitoring
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE system_monitoring;

CREATE TABLE system_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cpu_percentage JSON,
    cpu_total FLOAT,
    memory_total FLOAT,
    memory_used FLOAT,
    memory_available FLOAT,
    disk_read FLOAT,
    disk_write FLOAT,
    network_receive_mbps FLOAT,
    network_transmit_mbps FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;