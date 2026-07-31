"""Run before an interview or deployment to verify the project."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.database import database_health, init_db
from backend.services.document_parser import extract_text_from_bytes
from backend.services.resume_parser import parse_resume

required = [
    ROOT / "streamlit_app.py",
    ROOT / "backend" / "main.py",
    ROOT / "requirements.txt",
    ROOT / "sample_data" / "sample_final_year_resume.txt",
    ROOT / "sample_data" / "recruiter_demo_job_description.txt",
]

missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing required files:\n" + "\n".join(missing))

init_db(seed=True)
ok, backend = database_health()
if not ok:
    raise SystemExit(f"Database unavailable: {backend}")

sample = ROOT / "sample_data" / "sample_final_year_resume.txt"
text = extract_text_from_bytes(sample.read_bytes(), sample.name)
profile = parse_resume(text)
assert profile["name"]
assert len(profile["skills"]) >= 10

print("Preflight passed")
print(f"Database: {backend}")
print(f"Sample candidate: {profile['name']}")
print(f"Detected skills: {len(profile['skills'])}")
