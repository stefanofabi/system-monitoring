CREATE TABLE system_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cpu FLOAT,
    cpu_temp FLOAT,
    memory FLOAT,
    disk FLOAT,
    disk_read FLOAT,
    disk_write FLOAT,
    disk_wait FLOAT,
    network_receive FLOAT,
    network_transmit FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ip VARCHAR(255) NOT NULL,
    threshold INT NOT NULL,
    failed INT DEFAULT 0, 
    high-ping-count INT DEFAULT 0, 
    active BOOLEAN DEFAULT FALSE 
);

CREATE TABLE latencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL, 
    response_time FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
);

INSERT INTO sensors (name, ip, threshold)
VALUES
    ('CABASE', 'cabase.4evergaming.com.ar', 30),
    ('Stormwall', 'stormwall.4evergaming.com.ar', 250),
    ('Telecom Argentina', 'telecom.4evergaming.com.ar', 30),
    ('Claro', 'claro.4evergaming.com.ar', 30),
    ('Telecentro', 'telecentro.4evergaming.com.ar', 30),
    ('Gigared', 'gigared.4evergaming.com.ar', 30),
    ('Movistar', 'movistar.4evergaming.com.ar', 30);
