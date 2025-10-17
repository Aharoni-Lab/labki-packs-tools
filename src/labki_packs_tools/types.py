from datetime import datetime, UTC
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def _to_utc(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    value = value.replace(tzinfo=UTC)
    return value


def _to_isoformat(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


UTCDateTime = Annotated[datetime, BeforeValidator(_to_utc), PlainSerializer(_to_isoformat)]
