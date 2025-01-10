import psutil

# Functions to collect system information
def get_cpu_usage():
    cpu_total = psutil.cpu_percent(interval=1)
    return cpu_total

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            # On some systems, temperatures are reported under 'coretemp'
            temp = temps['coretemp'][0].current
        elif 'cpu_thermal' in temps:
            # On some systems, temperatures are reported under 'cpu_thermal'
            temp = temps['cpu_thermal'][0].current
        else:
            temp = None
    except (AttributeError, KeyError):
        temp = None
    return temp