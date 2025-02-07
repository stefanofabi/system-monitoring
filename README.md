# System Monitoring Script
This project is a [4evergaming](https://4evergaming.com.ar/status) system monitoring tool that runs on a local server and logs system usage data. The setup includes a Python virtual environment and a cron job to automatically run the script every 5 minutes.

## Requirements

- Python 3.x
- `pip`
- MySQL database
- Access to cron (to schedule the script execution)

## Installation
```bash
# Install linux dependencies
apt install git python3-venv lm-sensors -y

# Clone my repository
cd /root
git clone https://github.com/stefanofabi/system-monitoring.git
cd system-monitoring

# Enter the virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Install python dependencies
pip install -r requirements.txt

# Configure the MySQL database
cp config.json.example config.json
nano config.json

# Import the mysql database
mysql -u system_monitoring -p system_monitoring < /root/system-monitoring/database/structure.sql

# Run the script to verify that everything is ok
chmod +x run_stats.sh
./run_stats.sh

chmod +x run_ping.sh
./run_ping.sh
```

Then set up a cron every 5 minutes:
```bash
crontab -e

*/5 * * * * cd /root/system-monitoring && /root/system-monitoring/run_stats.sh > /root/system-monitoring/stats.log 2>&1

*/1 * * * * cd /root/system-monitoring && /root/system-monitoring/run_ping.sh > /root/system-monitoring/ping.log 2>&1

```
