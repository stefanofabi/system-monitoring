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
