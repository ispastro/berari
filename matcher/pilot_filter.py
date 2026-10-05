import re
from typing import Dict, Any, Optional, Tuple
from config import PILOT_KEYWORDS, CABIN_CREW_KEYWORDS, MAINTENANCE_KEYWORDS, EXCLUDED_KEYWORDS

class PilotFilter:
    """
    Intelligent aviation vacancy filter and classifier for Ethiopian Airlines.
    Categorizes positions into PILOT, CABIN_CREW, and MAINTENANCE tracks.
    """
    def __init__(self):
        self.pilot_keywords = [k.lower() for k in PILOT_KEYWORDS]
        self.cabin_keywords = [k.lower() for k in CABIN_CREW_KEYWORDS]
        self.maintenance_keywords = [k.lower() for k in MAINTENANCE_KEYWORDS]
        self.excluded_keywords = [k.lower() for k in EXCLUDED_KEYWORDS]

    def classify_vacancy(self, title: str, description: str = "") -> Tuple[Optional[str], Dict[str, Optional[str]]]:
        """
        Classifies a job posting into a category: 'PILOT', 'CABIN_CREW', 'MAINTENANCE', or None.
        Also extracts metadata (age, education, deadline, height).
        """
        title_lower = title.strip().lower()
        comb_lower = f"{title_lower} {description.lower()}"

        # 1. Pilot matching (highest priority)
        if any(pk in title_lower for pk in self.pilot_keywords):
            return "PILOT", self.extract_metadata(comb_lower)
        if "pilot" in title_lower and any(w in title_lower for w in ["trainee", "cadet", "student", "license", "initial", "admission", "course"]):
            return "PILOT", self.extract_metadata(comb_lower)

        # 2. Cabin Crew matching
        if any(ck in title_lower for ck in self.cabin_keywords):
            return "CABIN_CREW", self.extract_metadata(comb_lower)
        if "cabin" in title_lower and "crew" in title_lower:
            return "CABIN_CREW", self.extract_metadata(comb_lower)

        # 3. Aircraft Maintenance matching
        if any(mk in title_lower for mk in self.maintenance_keywords):
            return "MAINTENANCE", self.extract_metadata(comb_lower)
        if ("aircraft" in title_lower or "aviation" in title_lower) and any(w in title_lower for w in ["technician", "mechanic", "maintenance", "avionics"]):
            return "MAINTENANCE", self.extract_metadata(comb_lower)

        # 4. Check body if title is ambiguous (e.g. "Cadet Program 2026", "Aviation Trainee Intake")
        if not any(ex in title_lower for ex in self.excluded_keywords):
            if any(pk in comb_lower for pk in ["pilot trainee", "trainee pilot", "commercial pilot license"]):
                return "PILOT", self.extract_metadata(comb_lower)
            if any(ck in comb_lower for ck in ["cabin crew trainee", "trainee flight attendant"]):
                return "CABIN_CREW", self.extract_metadata(comb_lower)
            if any(mk in comb_lower for mk in ["aircraft maintenance technician", "trainee technician"]):
                return "MAINTENANCE", self.extract_metadata(comb_lower)

        return None, self.extract_metadata(comb_lower)

    def is_pilot_trainee_vacancy(self, title: str, description: str = "") -> bool:
        """Backwards-compatible helper specifically checking for pilot positions."""
        category, _ = self.classify_vacancy(title, description)
        return category == "PILOT"

    def extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """Parse requirements from description."""
        metadata: Dict[str, Optional[str]] = {
            "age": None,
            "education": None,
            "deadline": None,
            "height": None,
        }

        if not text:
            return metadata

        # Age pattern (e.g. "Age: 18 - 25", "Age limit: between 18 and 25 years", "maximum age of 30")
        age_match = re.search(
            r'(?:age|aged)(?:\s*(?:limit|requirement|criteria))?\s*[:\-–]?\s*(?:between\s+)?(\d{2}\s*(?:-|to|and)\s*\d{2}|\b\d{2}\b\s*years?)',
            text,
            re.I
        )
        if age_match:
            metadata["age"] = age_match.group(0).strip()

        # Education pattern (e.g. "BSc / BA degree", "Diploma", "10+2", "CGPA 2.75")
        edu_match = re.search(r'(?:degree|bsc|ba|b\.sc|b\.a|cgpa|gpa|diploma|grade\s*12)[^\n.]{5,80}', text, re.I)
        if edu_match:
            metadata["education"] = edu_match.group(0).strip()

        # Deadline pattern (e.g. "Closing Date: 15 October 2026", "Deadline: ...")
        deadline_match = re.search(r'(?:deadline|closing\s*date|apply\s*before|valid\s*until)[^\w\n]{1,15}([A-Za-z0-9\s,/-]{4,30})', text, re.I)
        if deadline_match:
            metadata["deadline"] = deadline_match.group(1).strip()

        # Height pattern (e.g. "Height: minimum 1.62m", "minimum height: 165 cm", "Height minimum 1.62m")
        height_match = re.search(
            r'(?:height|minimum\s+height)(?:\s*(?:limit|requirement|minimum|of|is))*\s*[:\-–]?\s*(\d(?:\.\d{1,2})?\s*(?:m|cm|meters))',
            text,
            re.I
        )
        if height_match:
            metadata["height"] = height_match.group(1).strip()

        return metadata
