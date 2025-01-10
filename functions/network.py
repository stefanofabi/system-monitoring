import psutil
import time

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