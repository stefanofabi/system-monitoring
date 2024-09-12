# System Monitoring Script

This project is a system monitoring tool that runs on a server and logs system usage data. The setup includes a Python virtual environment and a cron job to automatically run the script every 5 minutes.

## Requirements

- Python 3.x
- `pip`
- Access to cron (to schedule the script execution)

## Installation
```bash
apt install python3.11-venv lm-sensors -y

git clone https://github.com/stefanofabi/system-monitoring.git
cd system-monitoring
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

chmod +x run_monitor.sh
```

Then set up a cron every 5 minutes:
```bash
crontab -e

*/5 * * * * cd /root/system-monitoring && /root/system-monitoring/run_monitor.sh >> /root/system-monitoring/monitor.log 2>&1

```
