import pytest

from src.utils.utils import min_to_sec, parse_initial_countdown


#
# -----------------------
#  TEST: min_to_sec
# -----------------------
#

@pytest.mark.parametrize("input_str,expected", [
    ("10:00", 600),       # Standard mm:ss format
    ("05:30", 330),       # Standard mm:ss format with non-zero seconds
    ("0:45", 45),         # Less than a minute
    ("0:00", 0),          # Edge case: zero time
    ("123", 123),         # Direct integer input
    ("00:10", 10),        # Leading zeros in mm:ss format
])
def test_min_to_sec(input_str, expected):
    """Test the conversion of time strings to seconds."""
    assert min_to_sec(input_str) == expected

#
# -------------------------------
#  TEST: parse_initial_countdown
# -------------------------------
#

@pytest.mark.parametrize("input_str,expected", [
    # mm:ss format, positive countdown
    ("10:00", -600),     # Game hasn't started yet
    ("05:30", -330),     # Non-zero seconds countdown

    # mm:ss format, negative countdown
    ("-10:00", 600),     # Game already started 10 minutes ago
    ("-05:30", 330),     # Game already started 5:30 minutes ago

    # Integer inputs
    ("300", -300),       # Positive countdown in seconds
    ("-120", 120),       # Negative elapsed time in seconds

    # Edge cases
    ("0:00", 0),         # Game starts exactly at 0
    ("0", 0),            # Single zero input
    ("-0:30", 30),       # Elapsed time less than a minute
])
def test_parse_initial_countdown(input_str, expected):
    """Test parsing of initial countdown strings."""
    assert parse_initial_countdown(input_str) == expected
