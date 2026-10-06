from datetime import datetime
from zoneinfo import ZoneInfo

def get_datetime_local():
    return datetime.now(ZoneInfo("Europe/Stockholm")).replace(tzinfo=None)