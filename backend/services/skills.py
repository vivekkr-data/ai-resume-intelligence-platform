"""Skill taxonomy and deterministic skill extraction."""
from __future__ import annotations

import re
from collections import defaultdict

SKILL_CATEGORIES: dict[str, list[str]] = {
    "Programming": [
        "Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript",
        "R", "Go", "Rust", "PHP", "Kotlin", "Swift", "Scala", "SQL",
        "Bash", "MATLAB",
    ],
    "AI & Machine Learning": [
        "Machine Learning", "Deep Learning", "Natural Language Processing",
        "Computer Vision", "Generative AI", "Large Language Models",
        "Prompt Engineering", "Reinforcement Learning",
        "Recommendation Systems", "Time Series", "Feature Engineering",
        "Model Evaluation", "Transfer Learning", "Transformers",
        "Sentence Transformers", "Semantic Search", "Cosine Similarity", "BERT",
        "Retrieval Augmented Generation", "Scikit-learn", "TensorFlow", "PyTorch",
        "Keras", "XGBoost", "LightGBM", "Hugging Face", "OpenCV", "spaCy",
        "NLTK", "LangChain", "LlamaIndex",
    ],
    "Data": [
        "Data Analysis", "Data Science", "Data Visualization", "Statistics",
        "Pandas", "NumPy", "Matplotlib", "Power BI", "Tableau", "Excel",
        "ETL", "Data Mining", "A/B Testing", "Apache Spark", "Hadoop",
        "Kafka", "Airflow",
    ],
    "Backend & Web": [
        "FastAPI", "Flask", "Django", "REST API", "GraphQL", "Node.js",
        "Express.js", "React", "Next.js", "HTML", "CSS", "Streamlit",
        "Microservices", "SQLAlchemy", "Pydantic", "Uvicorn", "Pytest",
        "JWT", "OAuth", "WebSocket", "Alembic",
    ],
    "Databases": [
        "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
        "Oracle", "SQL Server", "Vector Database", "Pinecone", "FAISS",
        "ChromaDB", "Neon", "Supabase",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Git",
        "GitHub", "GitLab", "CI/CD", "Linux", "Terraform", "MLflow", "DVC",
        "MLOps", "Model Deployment", "Render", "Heroku", "GitHub Actions",
        "Streamlit Community Cloud",
    ],
    "Professional": [
        "Problem Solving", "Communication", "Teamwork", "Leadership",
        "Agile", "Scrum", "Project Management", "Critical Thinking",
    ],
}

ALIASES: dict[str, str] = {
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "postgres": "PostgreSQL",
    "postgre sql": "PostgreSQL",
    "js": "JavaScript",
    "ts": "TypeScript",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "expressjs": "Express.js",
    "nextjs": "Next.js",
    "powerbi": "Power BI",
    "huggingface": "Hugging Face",
    "hugging face transformers": "Transformers",
    "large language model": "Large Language Models",
    "large language models": "Large Language Models",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "nlp": "Natural Language Processing",
    "gen ai": "Generative AI",
    "genai": "Generative AI",
    "restful api": "REST API",
    "rest apis": "REST API",
    "rag": "Retrieval Augmented Generation",
    "retrieval-augmented generation": "Retrieval Augmented Generation",
    "github action": "GitHub Actions",
    "github workflow": "GitHub Actions",
    "postgresql database": "PostgreSQL",
    "google cloud platform": "GCP",
    "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD",
}

CANONICAL_TO_CATEGORY: dict[str, str] = {}
for category, values in SKILL_CATEGORIES.items():
    for value in values:
        CANONICAL_TO_CATEGORY[value] = category


def _pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term).replace(r"\ ", r"[\s\-/.]+")
    if term in {"C", "R", "Go"}:
        return re.compile(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", re.I)
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.I)


SEARCH_TERMS: list[tuple[re.Pattern[str], str]] = []
_seen: set[tuple[str, str]] = set()
for canonical in CANONICAL_TO_CATEGORY:
    key = (canonical.lower(), canonical)
    if key not in _seen:
        SEARCH_TERMS.append((_pattern(canonical), canonical))
        _seen.add(key)
for alias, canonical in ALIASES.items():
    key = (alias.lower(), canonical)
    if key not in _seen:
        SEARCH_TERMS.append((_pattern(alias), canonical))
        _seen.add(key)


def extract_skills(text: str) -> list[str]:
    found = {canonical for pattern, canonical in SEARCH_TERMS if pattern.search(text)}

    # Avoid duplicate concepts in presentation.

    return sorted(found, key=str.lower)


def group_skills(skills: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for skill in skills:
        grouped[CANONICAL_TO_CATEGORY.get(skill, "Other")].append(skill)
    return {category: sorted(values) for category, values in grouped.items()}
