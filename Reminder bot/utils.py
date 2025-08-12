# utils.py

def format_mention(user_id: int) -> str:
    return f"<@{user_id}>"

def is_valid_time_format(time_str: str) -> bool:
    # Basic check for HH:MM format
    import re
    return bool(re.match(r"^\d{2}:\d{2}$", time_str))

# You can add more reusable functions here
