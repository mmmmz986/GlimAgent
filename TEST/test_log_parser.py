import json
import unittest

from CORE.log_parser import decode_log, entries_to_json, parse_log


class LogParserTests(unittest.TestCase):
    def test_equipment_format(self):
        text = (
            "[2026/09/09] [00:10:31]\tCODE_487\t[Chart Reset] 그래프 append 4개 생략(lock 충돌)\r\n"
            "[2026/09/09] [00:10:42]\t102\t[LotChange][SkipWait] CurRW: 13.6\r\n"
            "[2026/09/09] [00:10:31]\t502\tNumber of received Frame data -> Client1 : 7985"
        )
        entries = parse_log(text)
        self.assertTrue(all(e.status == "parsed" for e in entries))
        self.assertEqual(entries[0].timestamp, "2026-09-09 00:10:31")
        self.assertEqual(entries[0].code, "CODE_487")
        self.assertIsNone(entries[0].level)
        self.assertEqual(entries[0].tags, ("Chart Reset",))
        self.assertEqual(entries[1].tags, ("LotChange", "SkipWait"))
        self.assertEqual(entries[2].tags, ())
        self.assertEqual([e.raw for e in entries], text.splitlines())

    def test_invalid_equipment_date_is_preserved(self):
        raw = "[2026/99/09] [00:10:31]\t502\tmessage"
        entry = parse_log(raw)[0]
        self.assertEqual(entry.status, "unparsed")
        self.assertEqual(entry.raw, raw)

    def test_timestamp_levels_and_original_lines(self):
        text = "[2026-09-15 10:20:30.123] [INFO] 시작\n2026-09-15T10:20:31+09:00 ERROR 정지"
        entries = parse_log(text)
        self.assertEqual(entries[0].message, "시작")
        self.assertEqual(entries[1].level, "ERROR")
        self.assertEqual(entries[1].line_number, 2)
        self.assertEqual(entries[1].timestamp, "2026-09-15T10:20:31+09:00")
        self.assertEqual([e.raw for e in entries], text.splitlines())

    def test_unknown_blank_and_trace_lines_are_preserved(self):
        text = 'unknown ERROR inside message\n\n  File "app.py", line 12\nINFO ready'
        entries = parse_log(text)
        self.assertEqual(len(entries), 4)
        self.assertIsNone(entries[0].level)
        self.assertEqual(entries[1].raw, "")
        self.assertEqual(entries[2].status, "unparsed")
        self.assertEqual(entries[3].status, "partial")
        self.assertEqual(json.loads(entries_to_json(entries))[2]["raw"], text.splitlines()[2])

    def test_encoding_round_trips(self):
        for encoding in ("utf-8-sig", "cp949", "utf-16"):
            with self.subTest(encoding=encoding):
                self.assertEqual(decode_log("설비 정지".encode(encoding))[0], "설비 정지")

    def test_decode_failure_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            decode_log(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            decode_log(b"\xff", "utf-8-sig")

    def test_empty_file(self):
        self.assertEqual(parse_log(""), [])


if __name__ == "__main__":
    unittest.main()
