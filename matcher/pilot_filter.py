import re
from typing import Dict, Any, Optional
from config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS

class PilotFilter:
    def __init__(self):
        self.positive_keywords = [k.lower() for k in POSITIVE_KEYWORDS]
        self.negative_keywords = [k.lower() for k in NEGATIVE_KEYWORDS]

    def is_pilot_trainee_vacancy(self, title: str, description: str = "") -> bool:
        """
        Determine with high precision whether a vacancy is for a pilot trainee/cadet program.
        """
        combined_text = f"{title} {description}".lower()
        title_lower = title.lower()

        # Check positive keywords in title first (highest weight)
        title_match = any(pk in title_lower for pk in self.positive_keywords)

        # Check negative keywords
        negative_match = any(nk in title_lower for nk in self.negative_keywords)

        # If title clearly matches pilot trainee keywords, prioritize it even if negative words appear in body
        if title_match:
            # Only reject if title specifically says cabin crew or technician
            if "technician" in title_lower or "cabin crew" in title_lower or "flight attendant" in title_lower:
                return False
            return True

        # If not matched directly in title, check if "pilot" and ("trainee" or "cadet" or "student") appear in title
        if "pilot" in title_lower and any(w in title_lower for w in ["trainee", "cadet", "student", "initial", "admission", "license"]):
            return True

        # Check description if title is ambiguous (e.g. "Cadet Program 2026" or "Flight Operations Trainee")
        if any(pk in combined_text for pk in ["pilot trainee", "trainee pilot", "cadet pilot"]):
            if not negative_match:
                return True

        return False

    def extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse common requirements from the vacancy description text.
        """
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
        edu_match = re.search(r'(?:degree|bsc|ba|b\.sc|b\.a|cgpa|gpa|diploma)[^\n.]{5,80}', text, re.I)
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
