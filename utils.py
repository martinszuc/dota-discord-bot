def parse_time(time_str):
    """Convert time in 'mm:ss' format or seconds to total seconds."""
    if ":" in time_str:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    return int(time_str)

def mention_players(target_groups, usernames):
    """Generate mentions for target player groups."""
    # Map player positions to discord.Member objects
    position_map = {
        "safe": [usernames[0], usernames[4]],
        "mid": [usernames[1]],
        "off": [usernames[2], usernames[3]],
        "supps": [usernames[3], usernames[4]],
        "cores": [usernames[0], usernames[1], usernames[2]],
        "all": usernames,
        "1": [usernames[0]],
        "2": [usernames[1]],
        "3": [usernames[2]],
        "4": [usernames[3]],
        "5": [usernames[4]]
    }

    # Collect unique mentions from each target group
    mentioned_users = set()
    for group in target_groups:
        mentioned_users.update(position_map.get(group, []))

    # Use the 'mention' attribute for proper mentions
    mentions = [user.mention for user in mentioned_users]
    return " ".join(mentions) if mentions else ""
