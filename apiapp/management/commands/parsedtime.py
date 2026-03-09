from datetime import datetime, timedelta
import re

def parse_time_ago(time_str):
    """ Parse the 'X time ago' string and return the actual timestamp """
    now = datetime.now()
        # pattern = r"(\d+)\s*(h|hour|hours|m|min|minute|minutes|s|sec|seconds|d|day|days|month|months)?\s*(ago)?"


    match = re.match(r"(\d+)\s*(h|hour|hours|m|min|minute|minutes|s|sec|seconds|d|day|days|month|months)?\s*(ago)?", time_str.lower())
    if match:
        number = int(match.group(1))
        unit = match.group(2)

        if unit in ["s", "sec", "seconds"]:
            return now - timedelta(seconds=number)
        elif unit in ["m", "min", "minute", "minutes"]:
            return now - timedelta(minutes=number)
        elif unit in ["h", "hour", "hours"]:
            return now - timedelta(hours=number)
        elif unit in ["d", "day", "days"]:
            return now - timedelta(days=number)
        elif unit == 'week':
            return now - timedelta(weeks=number)
        elif unit in ["month", "months"]:
            return now - timedelta(weeks=number*4)  # Approximation
        elif unit in ["year", "years","y"]:
            return now - timedelta(weeks=number*52)  # Approximation
    return now 