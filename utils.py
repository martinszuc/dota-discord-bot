def parse_time(time_str):
    """Convert time in 'mm:ss' format or seconds to total seconds."""
    if ":" in time_str:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    return int(time_str)