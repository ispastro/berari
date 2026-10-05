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

    def test_positive_trainee_pilot_titles(self):
        trainee_titles = [
            "Trainee Pilot - Ethiopian Airlines",
            "Pilot Trainee (ET-Sponsored)",
            "Cadet Pilot Training Program 2026",
            "First Officer Trainee",
            "Trainee First Officer",
        ]
        for t in trainee_titles:
            cat, _ = self.filter.classify_vacancy(t)
            self.assertEqual(cat, "PILOT", f"Failed to match pilot trainee: {t}")

    def test_positive_cabin_crew_trainee_titles(self):
        trainee_titles = [
            "Trainee Cabin Crew - Ethiopian Airlines",
            "Cabin Crew Trainee Intake",
            "Flight Attendant Trainee Announcement",
            "Trainee Air Hostess",
        ]
        for t in trainee_titles:
            cat, _ = self.filter.classify_vacancy(t)
            self.assertEqual(cat, "CABIN_CREW", f"Failed to match cabin crew trainee: {t}")

    def test_positive_maintenance_trainee_titles(self):
        trainee_titles = [
            "Trainee Aircraft Maintenance Technician (AMT)",
            "Aircraft Mechanic Trainee",
            "Aviation Maintenance Engineering Trainee",
            "Avionics Technician Trainee",
            "Trainee Technician",
        ]
        for t in trainee_titles:
            cat, _ = self.filter.classify_vacancy(t)
            self.assertEqual(cat, "MAINTENANCE", f"Failed to match maintenance trainee: {t}")

    def test_excluded_non_trainee_and_cpl_titles(self):
        non_trainee = [
            "Commercial Pilot License (CPL)",
            "Admission for Commercial Pilot License (CPL)",
            "Commercial Pilot",
            "Senior Captain B787",
            "Experienced First Officer",
            "Cabin Crew",
            "Senior Flight Attendant",
            "Aircraft Maintenance Technician",
            "Avionics Engineer",
            "Junior Ticketing & Customer Service Agent",
            "Baggage Handler",
            "Bartender",
            "Meeting Concierge",
            "Finance & Accounting Officer",
            "Call Center Agent",
        ]
        for t in non_trainee:
            cat, _ = self.filter.classify_vacancy(t)
            self.assertIsNone(cat, f"Incorrectly matched non-trainee/CPL title: {t}")

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
            title="Pilot Trainee",
            source="Ethiopian Airlines Official Careers",
            category="PILOT",
            url="https://corporate.ethiopianairlines.com/job1",
            deadline="30 Oct 2026",
            summary="Requirements here"
        )
        self.assertTrue(res1["is_new"])

        res2 = self.db.upsert_vacancy(
            title="Pilot Trainee",
            source="Ethiopian Airlines Official Careers",
            category="PILOT",
            url="https://corporate.ethiopianairlines.com/job1",
        )
        self.assertFalse(res2["is_new"])

    def test_subscriber_track_filtering(self):
        self.db.add_subscriber(chat_id="101", username="pilot_guy", first_name="Abebe", track="PILOT")
        self.db.add_subscriber(chat_id="102", username="cabin_girl", first_name="Sara", track="CABIN_CREW")
        self.db.add_subscriber(chat_id="103", username="all_jobs", first_name="Dawit", track="ALL")

        pilot_subs = self.db.get_subscribers_for_category("PILOT")
        self.assertIn("101", pilot_subs)
        self.assertNotIn("102", pilot_subs)
        self.assertIn("103", pilot_subs)

        cabin_subs = self.db.get_subscribers_for_category("CABIN_CREW")
        self.assertNotIn("101", cabin_subs)
        self.assertIn("102", cabin_subs)
        self.assertIn("103", cabin_subs)

        tech_subs = self.db.get_subscribers_for_category("MAINTENANCE")
        self.assertNotIn("101", tech_subs)
        self.assertNotIn("102", tech_subs)
        self.assertIn("103", tech_subs)


if __name__ == "__main__":
    unittest.main()
