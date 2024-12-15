# utils.py

def min_to_sec(time_str):
    """Convert time in 'mm:ss' format or seconds to total seconds."""
    if ":" in time_str:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    return int(time_str)


def parse_initial_countdown(countdown_str):
    """
    Interprets an input string (like '10:00', '-05:30', '300', '-120') as either a positive countdown or
    a negative elapsed time. Returns the integer time_elapsed for the GameTimer.

    Positive countdown -> game not started yet, so we store negative of that number in time_elapsed.
    Negative countdown -> game is already X seconds in, so time_elapsed = positive integer.
    """
    # First, let's unify everything in seconds
    raw_seconds = 0
    if ":" in countdown_str:
        # 'mm:ss' format
        negative = countdown_str.startswith("-")
        # Remove any leading '-'
        time_str = countdown_str[1:] if negative else countdown_str
        minutes, seconds = map(int, time_str.split(":"))
        raw_seconds = minutes * 60 + seconds
        if negative:
            # Means the game has already elapsed raw_seconds
            return raw_seconds
        else:
            # Means the game is not started yet, so store negative
            return -raw_seconds
    else:
        # It's a signed or unsigned integer in seconds
        if countdown_str.startswith("-"):
            val = abs(int(countdown_str))
            return val  # Already elapsed
        else:
            val = int(countdown_str)
            return -val  # Counting down
