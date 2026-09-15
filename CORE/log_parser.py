"""Conservative, line-oriented log parsing without external dependencies."""

from dataclasses import asdict, dataclass
import json
import re
from datetime import datetime


EQUIPMENT_LINE = re.compile(
    r"^\[(?P<date>\d{4}/\d{2}/\d{2})\]\s+\[(?P<time>\d{2}:\d{2}:\d{2})\]"
    r"[ \t]+(?P<code>\d+|CODE_\d+)[ \t]+(?P<message>.*)$"
)
TIMESTAMP = re.compile(
    r"^\s*\[?(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[ T]"
    r"\d{2}:\d{2}:\d{2}(?:[.,]\d{1,9})?(?:Z|[+-]\d{2}:?\d{2})?)\]?"
)
LEVEL = re.compile(
    r"^\s*(?:[-|:]\s*)?(?:\[(?P<bracket>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]"
    r"|(?P<plain>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b)\s*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LogEntry:
    line_number: int
    timestamp: str | None
    level: str | None
    message: str
    raw: str
    status: str
    code: str | None = None
    tags: tuple[str, ...] = ()


def decode_log(data: bytes, encoding: str = "auto") -> tuple[str, str]:
    """Decode strictly: never silently discard or replace log characters."""
    if encoding != "auto":
        return data.decode(encoding), encoding
    
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    
    for candidate in ("utf-8-sig", "cp949"):
        try:
            return data.decode(candidate), candidate
        except UnicodeDecodeError:
            continue
    raise ValueError("UTF-8 또는 CP949로 읽을 수 없습니다. 파일 인코딩을 확인하세요.")


def parse_log(text: str) -> list[LogEntry]:
    """Keep every physical line, including blanks and stack-trace lines.

    Only a leading timestamp and a following/leading level are interpreted.
    Unknown layouts remain available in raw/message for format-specific parsing.
    """
    entries = []
    for number, raw in enumerate(text.splitlines(), start=1):
        
        equipment_match = EQUIPMENT_LINE.match(raw)
        if equipment_match:
            fields = equipment_match.groupdict()
            try:
                timestamp = datetime.strptime(
                    f"{fields['date']} {fields['time']}", "%Y/%m/%d %H:%M:%S"
                ).isoformat(sep=" ")
            except ValueError:
                entries.append(LogEntry(number, None, None, raw, raw, "unparsed"))
                continue
            message = fields["message"]
            tag_prefix = re.match(r"^(?:\[[^\]\r\n]+\])+", message)
            tags = tuple(re.findall(r"\[([^\]]+)\]", tag_prefix.group())) if tag_prefix else ()
            entries.append(LogEntry(number, timestamp, None, message, raw, "parsed", fields["code"], tags))
            continue

        remainder = raw

        timestamp = None
        timestamp_match = TIMESTAMP.match(remainder)
        if timestamp_match:
            timestamp = timestamp_match.group("timestamp")
            remainder = remainder[timestamp_match.end():]

        level = None
        level_match = LEVEL.match(remainder)
        if level_match:
            level = (level_match.group("bracket") or level_match.group("plain")).upper()
            remainder = remainder[level_match.end():]
            
        status = "parsed" if timestamp and level else "partial" if timestamp or level else "unparsed"
        entries.append(LogEntry(number, timestamp, level, remainder.strip(), raw, status))
    return entries


def entries_to_json(entries: list[LogEntry]) -> str:
    return json.dumps([asdict(entry) for entry in entries], ensure_ascii=False, indent=2)
