import re
from datetime import datetime, date
from zoneinfo import ZoneInfo

def get_datetime_local():
    return datetime.now(ZoneInfo("Europe/Stockholm")).replace(tzinfo=None)

def parse_datetime_isoformat(date_str):
    return datetime.fromisoformat(date_str)

def clean_text(text: str) -> str:
    for ch in ("\xa0", "\u202f"):                
        text = text.replace(ch, " ")
    for ch in ("\ufeff", "\u200b", "\xad"):       
        text = text.replace(ch, "")
    text = re.sub(r"[ \t]+", " ", text)           
    text = re.sub(r" *\n *", "\n", text)       
    text = re.sub(r"\n{3,}", "\n\n", text)      
    return text.strip()