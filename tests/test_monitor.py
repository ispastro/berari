import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher.pilot_filter import PilotFilter
from database.db import Database

class TestPilotMatcher(unittest.TestCase):
    def setUp(self):
        self.filter = PilotFilter()

    def test_positive_pilot_titles(self):
        titles = [
            "Trainee Pilot - Ethiopian Airlines",
            "Pilot Trainee (ET-Sponsored)",
            "Cadet Pilot Training Program 2026",
            "Admission for Commercial Pilot License (CPL)",
            "Ab-initio Pilot Course Announcement",
            "First Officer Trainee",
            "Commercial Pilot",
        ]
        for t in titles:
            self.assertTrue(self.filter.is_pilot_trainee_vacancy(t), f"Failed to match: {t}")

    def test_negative_non_pilot_titles(self):
        titles = [
            "Cabin Crew - Ethiopian Airlines",
            "Flight Attendant Trainee",
            "Aircraft Maintenance Technician",
            "Aircraft Mechanic II",
            "Junior Ticketing & Customer Service Agent",
            "Baggage Handler",
            "Finance & Accounting Officer",
            "IT Systems Administrator",
        ]
        for t in titles:
            self.assertFalse(self.filter.is_pilot_trainee_vacancy(t), f"Incorrectly matched: {t}")

    def test_metadata_extraction(self):
        sample_text = (
            "Ethiopian Airlines invites applicants for Pilot Trainee position. "
            "Educational Qualification: BSc degree in Engineering with minimum CGPA 2.75. "
            "Age limit: between 18 and 25 years. "
            "Physical: Height minimum 1.62m. "
            "Registration Deadline: 20 November 2026."
        )
        meta = self.filter.extract_metadata(sample_text)
        self.assertIsNotNone(meta["age"])
        self.assertIn("18", meta["age"])
        self.assertIsNotNone(meta["education"])
        self.assertIn("degree", meta["education"].lower())
        self.assertIsNotNone(meta["height"])
        self.assertIn("1.62", meta["height"])
        self.assertIsNotNone(meta["deadline"])
        self.assertIn("20 November", meta["deadline"])


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = Database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upsert_and_deduplication(self):
        res1 = self.db.upsert_vacancy(
            title="Trainee Pilot",
            source="Ethiopian Airlines",
            url="https://corporate.ethiopianairlines.com/job1",
            deadline="30 Oct 2026",
            summary="Requirements here"
        )
        self.assertTrue(res1["is_new"])

        # Second insert with same title and url should recognize it as existing
        res2 = self.db.upsert_vacancy(
            title="Trainee Pilot",
            source="Ethiopian Airlines",
            url="https://corporate.ethiopianairlines.com/job1",
        )
        self.assertFalse(res2["is_new"])

    def test_subscribers(self):
        self.db.add_subscriber(chat_id="12345678", username="pilot_john", first_name="John")
        subs = self.db.get_active_subscribers()
        self.assertIn("12345678", subs)

        self.db.remove_subscriber("12345678")
        subs_after = self.db.get_active_subscribers()
        self.assertNotIn("12345678", subs_after)


if __name__ == "__main__":
    unittest.main()
