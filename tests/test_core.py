from backend.config import normalize_database_url
from backend.services import analyzer
from backend.services.resume_parser import parse_job_description, parse_resume
from backend.services.skills import extract_skills
from backend.services.suggestions import ats_checklist, resume_quality_score


RESUME = """
Jane Doe
jane@example.com | +91 98765 43210 | https://github.com/janedoe

SUMMARY
Final-year computer science student building NLP and machine-learning applications.

SKILLS
Python, SQL, Pandas, NumPy, Scikit-learn, FastAPI, Streamlit, Git

PROJECTS
• Built an NLP resume matching API with FastAPI and improved evaluation accuracy to 87%.
• Deployed a Streamlit dashboard that processed 5,000 records.

EDUCATION
B.Tech Computer Science, 2023 - 2027
"""

JD = """
AI Intern
Required: Python, Machine Learning, NLP, Scikit-learn, FastAPI, SQL and Git.
Preferred: PostgreSQL, Docker and Sentence Transformers.
No formal experience required.
"""


def test_skill_extraction_handles_aliases():
    text = "Built NLP APIs with sklearn, Postgres, NodeJS and HuggingFace transformers."
    skills = extract_skills(text)
    assert "Natural Language Processing" in skills
    assert "Scikit-learn" in skills
    assert "PostgreSQL" in skills
    assert "Node.js" in skills
    assert "Hugging Face" in skills


def test_resume_profile_and_ats_checks():
    profile = parse_resume(RESUME)
    assert profile["name"] == "Jane Doe"
    assert "Python" in profile["skills"]
    assert profile["has_projects"] is True
    assert profile["metric_count"] >= 2
    assert resume_quality_score(profile) > 60
    assert len(ats_checklist(profile)) == 8


def test_job_description_separates_required_and_preferred_skills():
    profile = parse_job_description(JD, "AI Intern")
    assert "Python" in profile["required_skills"]
    assert "PostgreSQL" in profile["preferred_skills"]
    assert "Docker" in profile["preferred_skills"]


def test_explainable_analysis_shape(monkeypatch):
    monkeypatch.setattr(
        analyzer,
        "semantic_similarity_detailed",
        lambda *_: (
            78.0,
            "test-model",
            [
                {
                    "requirement": "Build NLP APIs",
                    "resume_evidence": "Built an NLP resume matching API",
                    "similarity": 88.0,
                }
            ],
        ),
    )
    result = analyzer.analyze_resume(
        resume_text=RESUME,
        job_description=JD,
        filename="resume.txt",
        job_title="AI Intern",
    )
    assert result["scores"]["semantic"] == 78.0
    assert result["evidence"][0]["similarity"] == 88.0
    assert result["privacy"]["raw_resume_stored"] is False
    assert "PostgreSQL" in result["preferred_skill_gaps"]
    assert result["verdict"]


def test_database_url_normalization():
    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_database_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_database_url("sqlite:///test.db") == "sqlite:///test.db"
