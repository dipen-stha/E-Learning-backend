def format_to_mm_ss(given_time_in_seconds: int) -> str:
    minutes, seconds = divmod(given_time_in_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def format_to_seconds(given_time_format: str) -> int:
    minutes, seconds = map(int, given_time_format.split(":"))
    return minutes * 60 + seconds
