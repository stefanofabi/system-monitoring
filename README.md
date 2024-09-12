# System Monitoring Script

This project is a system monitoring tool that runs on a server and logs system usage data. The setup includes a Python virtual environment and a cron job to automatically run the script every 5 minutes.

## Requirements

- Python 3.x
- `pip`
- Access to cron (to schedule the script execution)

## Installation
$ git clone git@github.com:stefanofabi/system-monitoring.git
$ cd system-monitoring
$ python3 -m venv myenv
$ source myenv/bin/activate
$ pip install -r requirements.txt


Then set up a cron every 5 minutes:
*/5 * * * * /root/system-monitoring/run_monitor.sh >> /root/system-monitoring/monitor.log 2>&1
