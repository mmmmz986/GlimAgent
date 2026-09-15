"""Compare every JSON record with its original workbook row."""
import json
from pathlib import Path
import sys

import openpyxl


target = Path(__file__).resolve().parents[1] / "knowledge" / "log_reference.json"
data = json.loads(target.read_text(encoding="utf-8"))
workbook = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
rows = {sheet.title: list(sheet.values) for sheet in workbook}
expected_count = sum(
    1 for sheet_rows in rows.values() for row in sheet_rows
    if isinstance(row[0], (int, float)) and row[2] is not None
)
assert len(data["entries"]) == expected_count
for entry in data["entries"]:
    row = rows[entry["source"]["sheet"]][entry["source"]["row"] - 1]
    for key, value in zip(
        ["source_index", "category", "message_template", "code", "description"], row[:5]
    ):
        if key in ("source_index", "code") and value is not None:
            value = str(value)
        assert entry[key] == value, (entry["id"], key)
    alarm = entry["log_type"] == "alarm"
    assert entry["example"] == row[6 if alarm else 5]
    assert entry["recommended_action"] == (row[5] if alarm else None)
    assert entry["source_note"] == (None if alarm else row[6])
workbook.close()
print(f"Verified {expected_count} records against source; {target.stat().st_size} bytes")
