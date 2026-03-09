
from datetime import datetime

def get_time_difference(saved_time):
    # Get the current time (timezone-aware)
    now = datetime.now()  # timezone-aware datetime

    # If saved_time is naive, convert it to timezone-aware datetime
    # if saved_time.tzinfo is None:
    #     saved_time = make_aware(saved_time)  # Convert to timezone-aware using default timezone (UTC)

    # Calculate the time difference
    time_difference = now - saved_time

    # If the saved time is in the future, handle this case
    if time_difference.total_seconds() < 0:
        return saved_time

    # Get total seconds for more readable output
    total_seconds = int(time_difference.total_seconds())

    # Format the time difference for readability
    if total_seconds < 60:
        return f"{total_seconds} sec ago"
    elif total_seconds < 3600:
        return f"{total_seconds // 60} min ago"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600} hour ago"
    elif total_seconds < 604800:
        return f"{time_difference.days} day ago"
    else:
        return f"{saved_time.strftime('%Y-%m-%d %H:%M:%S')}"
