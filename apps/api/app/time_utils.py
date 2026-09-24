from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def today_beijing() -> date:
    return datetime.now(BEIJING_TZ).date()


def parse_date_value(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip().replace("/", "-").replace("年", "-").replace("月", "-").replace("日", "")
    parts = text.split("-")
    if len(parts) == 2 and len(parts[0]) == 4:
        text = f"{parts[0]}-{parts[1]}-01"
    return date.fromisoformat(text)
