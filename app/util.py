def calculate_time(total_seconds):
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    time = "{:d}:{:02d}".format(minutes, seconds)
    return time