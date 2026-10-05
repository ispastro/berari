import re
from typing import Dict, Any, Optional, Tuple
from config import TRAINEE_INDICATORS, EXCLUDED_KEYWORDS

class PilotFilter:
    """
    Strict Trainee Vacancy Filter for Ethiopian Airlines Corporate Careers.
    Enforces that every matched position is an official TRAINEE vacancy.
    Excludes self-sponsored CPL courses and non-trainee / experienced positions.
    """
    def __init__(self):
        self.trainee_indicators = [k.lower() for k in TRAINEE_INDICATORS]
        self.excluded_keywords = [k.lower() for k in EXCLUDED_KEYWORDS]

    def classify_vacancy(self, title: str, description: str = "") -> Tuple[Optional[str], Dict[str, Optional[str]]]:
        """
        Classifies a job posting into:
          - 'PILOT'        (Pilot Trainee, Cadet Pilot)
          - 'CABIN_CREW'   (Cabin Crew Trainee, Flight Attendant Trainee)
          - 'MAINTENANCE'  (Aircraft Maintenance Trainee, Technician Trainee)
          - None           (Non-trainee or excluded)
        """
        title_lower = title.strip().lower()
        comb_lower = f"{title_lower} {description.lower()}"

        # 1. Reject explicit exclusions (e.g. CPL courses, hotel staff, experienced roles)
        if any(ex in title_lower for ex in self.excluded_keywords):
            return None, self.extract_metadata(comb_lower)

        # 2. Strict Requirement: MUST be a Trainee or Cadet position
        is_trainee = any(ti in title_lower for ti in self.trainee_indicators)
        if not is_trainee:
            # Check description only if title contains 'cadet' or 'initial' or 'admission'
            if any(ti in comb_lower for ti in ["pilot trainee", "trainee pilot", "cabin crew trainee", "technician trainee"]):
                is_trainee = True
            else:
                return None, self.extract_metadata(comb_lower)

        # 3. Categorize Trainee Tracks
        # Pilot Trainee
        if any(w in title_lower for w in ["pilot", "first officer", "cadet"]):
            return "PILOT", self.extract_metadata(comb_lower)

        # Cabin Crew Trainee
        if any(w in title_lower for w in ["cabin", "flight attendant", "air hostess"]):
            return "CABIN_CREW", self.extract_metadata(comb_lower)

        # Aircraft Maintenance & Technician Trainee (AMT, Avionics, Airframe, Powerplant)
        if any(w in title_lower for w in [
            "aircraft maintenance", "amt", "avionics", "aircraft mechanic",
            "aircraft technician", "airframe", "powerplant", "aviation maintenance",
            "aeronautical", "aircraft engineer", "technician", "mechanic", "maintenance"
        ]) and "industrial" not in title_lower:
            return "MAINTENANCE", self.extract_metadata(comb_lower)

        # Check body text for category if title is just "Trainee"
        if "pilot" in comb_lower:
            return "PILOT", self.extract_metadata(comb_lower)
        if "cabin" in comb_lower:
            return "CABIN_CREW", self.extract_metadata(comb_lower)
        if any(w in comb_lower for w in [
            "aircraft maintenance", "amt", "avionics", "airframe", "powerplant", "aviation maintenance"
        ]) and "industrial" not in comb_lower:
            return "MAINTENANCE", self.extract_metadata(comb_lower)

        # If it is confirmed to be a Trainee position, default to MAINTENANCE
        if is_trainee:
            return "MAINTENANCE", self.extract_metadata(comb_lower)

        return None, self.extract_metadata(comb_lower)

    def is_pilot_trainee_vacancy(self, title: str, description: str = "") -> bool:
        """Helper checking specifically for Pilot Trainee."""
        category, _ = self.classify_vacancy(title, description)
        return category == "PILOT"

    def extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """Parse age, education, deadline, and height requirements."""
        metadata: Dict[str, Optional[str]] = {
            "age": None,
            "education": None,
            "deadline": None,
            "height": None,
        }

        if not text:
            return metadata

        # Age pattern (e.g. "Age: 18 - 25", "Age limit: between 18 and 25 years")
        age_match = re.search(
            r'(?:age|aged)(?:\s*(?:limit|requirement|criteria))?\s*[:\-–]?\s*(?:between\s+)?(\d{2}\s*(?:-|to|and)\s*\d{2}|\b\d{2}\b\s*years?)',
            text,
            re.I
        )
        if age_match:
            metadata["age"] = age_match.group(0).strip()

        # Education pattern (e.g. "BSc degree", "Diploma", "10+2", "CGPA 2.75")
        edu_match = re.search(r'(?:degree|bsc|ba|b\.sc|b\.a|cgpa|gpa|diploma|grade\s*12)[^\n.]{5,80}', text, re.I)
        if edu_match:
            metadata["education"] = edu_match.group(0).strip()

        # Deadline pattern (e.g. "Closing Date: 15 October 2026", "Deadline: ...")
        deadline_match = re.search(r'(?:deadline|closing\s*date|apply\s*before|valid\s*until|registration\s*date)[^\w\n]{1,15}([A-Za-z0-9\s,/-]{4,30})', text, re.I)
        if deadline_match:
            metadata["deadline"] = deadline_match.group(1).strip()

        # Height pattern (e.g. "Height: minimum 1.62m", "minimum height: 165 cm")
        height_match = re.search(
            r'(?:height|minimum\s+height)(?:\s*(?:limit|requirement|minimum|of|is))*\s*[:\-–]?\s*(\d(?:\.\d{1,2})?\s*(?:m|cm|meters))',
            text,
            re.I
        )
        if height_match:
            metadata["height"] = height_match.group(1).strip()

        return metadata
