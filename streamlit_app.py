"""Recruiter-ready Streamlit interface for the AI Resume Intelligence Platform."""
from __future__ import annotations

import html
import json
import secrets
import uuid
from datetime import timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from backend.config import BASE_DIR, settings
from backend.database import SessionLocal, database_health, init_db
from backend.models import AnalysisFeedback, AnalysisRecord, JobPosting
from backend.services.analyzer import analyze_resume
from backend.services.document_parser import DocumentParseError, extract_text_from_bytes
from backend.services.job_recommender import recommend_jobs
from backend.services.report import html_report, markdown_report

st.set_page_config(
    page_title="AI Resume Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 3rem; max-width: 1450px;}
    .hero {padding: 1.8rem 2rem; border-radius: 22px; background: linear-gradient(125deg,#0f172a,#312e81 58%,#2563eb); color:white; margin-bottom:1rem; box-shadow:0 14px 34px rgba(15,23,42,.22)}
    .hero h1 {margin:0 0 .4rem 0; font-size:2.4rem; letter-spacing:-.035em;}
    .hero p {margin:0; opacity:.9; font-size:1.03rem; max-width:900px;}
    .badge {display:inline-block; margin-top:.8rem; margin-right:.45rem; padding:.3rem .68rem; border:1px solid rgba(255,255,255,.35); border-radius:999px; font-size:.78rem; background:rgba(255,255,255,.1)}
    .skill-chip {display:inline-block; padding:.3rem .62rem; margin:.18rem; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:.84rem; border:1px solid #e0e7ff;}
    .missing-chip {background:#fff1f2; color:#be123c; border-color:#fecdd3;}
    .matched-chip {background:#ecfdf5; color:#047857; border-color:#a7f3d0;}
    .preferred-chip {background:#fffbeb; color:#92400e; border-color:#fde68a;}
    .panel {border:1px solid #e2e8f0; background:#fff; padding:1rem 1.15rem; border-radius:15px; margin:.3rem 0 .8rem 0;}
    .evidence {border-left:4px solid #6366f1; background:#f8fafc; padding:.8rem 1rem; border-radius:8px; margin:.6rem 0;}
    .muted {color:#64748b; font-size:.88rem;}
    .privacy {background:#f0fdf4; color:#166534; padding:.65rem .8rem; border:1px solid #bbf7d0; border-radius:10px; font-size:.85rem;}
    div[data-testid="stMetric"] {background:#ffffff; border:1px solid #e2e8f0; padding:12px; border-radius:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def bootstrap() -> tuple[bool, str]:
    try:
        init_db(seed=True)
        return database_health()
    except Exception as exc:  # deployment/database configuration failure
        return False, str(exc)


db_ok, db_detail = bootstrap()
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

SESSION_ID: str = st.session_state.session_id
SAMPLE_JD_PATH = BASE_DIR / "sample_data" / "recruiter_demo_job_description.txt"
if not SAMPLE_JD_PATH.exists():
    SAMPLE_JD_PATH = BASE_DIR / "sample_data" / "sample_job_description.txt"


def chips(items: list[str], css_class: str) -> None:
    if not items:
        st.caption("None detected")
        return
    markup = "".join(
        f'<span class="skill-chip {css_class}">{html.escape(str(item))}</span>'
        for item in items
    )
    st.markdown(markup, unsafe_allow_html=True)


def save_analysis(resume_text: str, job_description: str, filename: str, job_title: str):
    if not db_ok:
        return analyze_resume(
            resume_text=resume_text,
            job_description=job_description,
            filename=filename,
            job_title=job_title,
            session_id=SESSION_ID,
            db=None,
        )
    with SessionLocal() as db:
        return analyze_resume(
            resume_text=resume_text,
            job_description=job_description,
            filename=filename,
            job_title=job_title,
            session_id=SESSION_ID,
            db=db,
        )


def format_date(value) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def admin_unlocked() -> bool:
    if not settings.admin_dashboard_pin:
        return settings.environment == "development"
    entered = st.session_state.get("admin_pin", "")
    return bool(entered) and secrets.compare_digest(entered, settings.admin_dashboard_pin)


def safe_error(exc: Exception) -> None:
    st.error("The request could not be completed. Check the uploaded file and deployment configuration.")
    if settings.debug:
        st.exception(exc)
    else:
        with st.expander("Technical detail"):
            st.code(str(exc))


with st.sidebar:
    st.header("Project Console")
    st.caption(f"Version {settings.app_version}")
    st.write(f"**Semantic model:** `{settings.embedding_model.split('/')[-1]}`")
    st.write(f"**Database:** {settings.database_backend}")
    st.write(f"**Database health:** {'Connected' if db_ok else 'Unavailable'}")
    st.write(f"**Environment:** {settings.environment}")
    st.divider()
    st.markdown("**Scoring architecture**")
    st.caption("60% semantic alignment")
    st.caption("25% required-skill coverage")
    st.caption("10% experience alignment")
    st.caption("5% ATS/resume quality")
    st.divider()
    st.markdown(
        "<div class='privacy'><b>Privacy by design</b><br>Raw resume text is never saved. Personal data is masked in database history unless STORE_PII=true.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="hero">
      <h1>AI Resume Intelligence Platform</h1>
      <p>Explainable semantic job matching, ATS quality analysis, skill-gap planning, PostgreSQL history and database-backed job recommendations.</p>
      <span class="badge">Sentence Transformers</span>
      <span class="badge">FastAPI</span>
      <span class="badge">PostgreSQL</span>
      <span class="badge">SQLAlchemy</span>
      <span class="badge">Responsible AI</span>
    </div>
    """,
    unsafe_allow_html=True,
)

analyzer_tab, jobs_tab, history_tab, recruiter_tab, system_tab = st.tabs(
    [
        "📄 Analyze Resume",
        "🎯 Job Matches",
        "🕘 My Analyses",
        "📊 Recruiter Dashboard",
        "🧩 System Design",
    ]
)

with analyzer_tab:
    top_left, top_right = st.columns([1, 1], gap="large")
    with top_left:
        uploaded = st.file_uploader(
            "Upload candidate resume",
            type=["pdf", "docx", "txt"],
            help="Text-based PDF, DOCX and TXT are supported. Maximum size is configured in .env.",
            key="analysis_resume",
        )
        job_title = st.text_input("Target job title", "AI / Machine Learning Intern")
        use_demo = st.button("Load recruiter demo job description", use_container_width=True)
        if use_demo:
            st.session_state.demo_jd = SAMPLE_JD_PATH.read_text(encoding="utf-8")
    with top_right:
        job_description = st.text_area(
            "Job description",
            height=285,
            value=st.session_state.get("demo_jd", ""),
            placeholder="Paste responsibilities, must-have skills, preferred skills, education and experience requirements...",
        )

    if st.button("🚀 Run Explainable Analysis", type="primary", use_container_width=True):
        if uploaded is None:
            st.error("Upload a resume first.")
        elif len(job_description.strip()) < 30:
            st.error("Paste a meaningful job description of at least 30 characters.")
        else:
            try:
                with st.spinner("Extracting profile, generating embeddings and building evidence..."):
                    resume_text = extract_text_from_bytes(uploaded.getvalue(), uploaded.name)
                    st.session_state.latest_analysis = save_analysis(
                        resume_text, job_description, uploaded.name, job_title
                    )
                st.success("Analysis completed" + (" and saved to the configured database." if db_ok else ". Database was unavailable, so this result was not persisted."))
            except DocumentParseError as exc:
                st.error(str(exc))
            except Exception as exc:
                safe_error(exc)

    result = st.session_state.get("latest_analysis")
    if result:
        scores = result["scores"]
        st.markdown(f"## {result['verdict']}")
        metrics = st.columns(5)
        for column, (label, key) in zip(
            metrics,
            [
                ("Overall fit", "overall"),
                ("Semantic", "semantic"),
                ("Skills", "skills"),
                ("Experience", "experience"),
                ("ATS quality", "resume_quality"),
            ],
        ):
            column.metric(label, f"{scores[key]:.1f}%")
        st.progress(scores["overall"] / 100, text=f"Overall recruiter-fit estimate: {scores['overall']:.1f}%")
        st.caption(
            f"Model: {result['model_used']} · Processing: {result['processing_ms']} ms · Analysis ID: {result.get('analysis_id')}"
        )

        chart_data = pd.DataFrame(
            {
                "Component": ["Semantic", "Skills", "Experience", "ATS quality"],
                "Score": [
                    scores["semantic"],
                    scores["skills"],
                    scores["experience"],
                    scores["resume_quality"],
                ],
            }
        ).set_index("Component")
        st.bar_chart(chart_data, height=260)

        matched_col, missing_col, preferred_col = st.columns(3)
        with matched_col:
            st.markdown("#### ✅ Matched required skills")
            chips(result["matched_skills"], "matched-chip")
        with missing_col:
            st.markdown("#### ⚠️ Missing required skills")
            chips(result["missing_skills"], "missing-chip")
        with preferred_col:
            st.markdown("#### ⭐ Preferred skill gaps")
            chips(result.get("preferred_skill_gaps", []), "preferred-chip")

        st.markdown("### Recruiter-ready candidate summary")
        summary_left, summary_right = st.columns([1, 1.35], gap="large")
        with summary_left:
            profile = result["resume_profile"]
            with st.container(border=True):
                st.write(f"**Candidate:** {profile.get('name') or 'Not detected'}")
                st.write(f"**Experience detected:** {profile.get('experience_years', 0):g} years")
                st.write(f"**Resume length:** {profile.get('word_count', 0)} words")
                st.write(f"**Sections:** {', '.join(profile.get('sections_found', [])) or 'Not detected'}")
                st.write(f"**Model evidence:** {len(result.get('evidence', []))} aligned requirement chunks")
                with st.expander("Extracted skill groups"):
                    for category, values in profile.get("skill_groups", {}).items():
                        st.write(f"**{category}:** {', '.join(values)}")
        with summary_right:
            st.markdown("#### Candidate strengths")
            if result.get("strengths"):
                for item in result["strengths"]:
                    st.success(item, icon="✅")
            else:
                st.info("No strong evidence was detected yet; use the improvement plan below.")

        st.markdown("### Explainable semantic evidence")
        st.caption("Each job requirement chunk is aligned to the closest resume evidence using embedding similarity.")
        for item in result.get("evidence", []):
            st.markdown(
                f"""
                <div class="evidence">
                  <b>{item['similarity']:.1f}% semantic alignment</b><br>
                  <span class="muted"><b>Job requirement:</b> {html.escape(item['requirement'])}</span><br>
                  <span><b>Resume evidence:</b> {html.escape(item['resume_evidence'])}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        checklist_col, plan_col = st.columns([1, 1.1], gap="large")
        with checklist_col:
            st.markdown("### ATS checklist")
            checklist_df = pd.DataFrame(
                [
                    {
                        "Status": "PASS" if item["passed"] else "IMPROVE",
                        "Check": item["check"],
                        "Why it matters": item["detail"],
                    }
                    for item in result.get("ats_checks", [])
                ]
            )
            st.dataframe(checklist_df, use_container_width=True, hide_index=True)
        with plan_col:
            st.markdown("### Improvement plan")
            for index, suggestion in enumerate(result.get("suggestions", []), 1):
                st.write(f"**{index}.** {suggestion}")

        if result.get("learning_roadmap"):
            st.markdown("### Skill-gap learning roadmap")
            st.dataframe(
                pd.DataFrame(result["learning_roadmap"]),
                use_container_width=True,
                hide_index=True,
            )

        report_json = json.dumps(result, indent=2, ensure_ascii=False)
        download_columns = st.columns(3)
        download_columns[0].download_button(
            "Download JSON",
            data=report_json,
            file_name="resume_intelligence_report.json",
            mime="application/json",
            use_container_width=True,
        )
        download_columns[1].download_button(
            "Download Markdown",
            data=markdown_report(result),
            file_name="resume_intelligence_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        download_columns[2].download_button(
            "Download HTML report",
            data=html_report(result),
            file_name="resume_intelligence_report.html",
            mime="text/html",
            use_container_width=True,
        )

        st.markdown("#### Was this analysis useful?")
        feedback_cols = st.columns([1, 1, 4])
        analysis_id = result.get("analysis_id")
        if analysis_id and feedback_cols[0].button("👍 Helpful", key=f"yes_{analysis_id}"):
            with SessionLocal() as db:
                db.add(AnalysisFeedback(analysis_id=analysis_id, helpful=True))
                db.commit()
            st.toast("Feedback saved")
        if analysis_id and feedback_cols[1].button("👎 Improve", key=f"no_{analysis_id}"):
            with SessionLocal() as db:
                db.add(AnalysisFeedback(analysis_id=analysis_id, helpful=False))
                db.commit()
            st.toast("Feedback saved")

with jobs_tab:
    st.write(
        "The resume is ranked against active PostgreSQL job postings using 75% semantic fit and 25% skill coverage. The bundled catalog contains demonstration roles, not live vacancies."
    )
    recommendation_resume = st.file_uploader(
        "Upload resume for role recommendations",
        type=["pdf", "docx", "txt"],
        key="recommendation_resume",
    )
    top_k = st.slider("Recommendations", 3, 10, 5)
    if st.button("Find Suitable Roles", type="primary", use_container_width=True):
        if recommendation_resume is None:
            st.error("Upload a resume first.")
        else:
            try:
                with st.spinner("Ranking database job postings..."):
                    resume_text = extract_text_from_bytes(
                        recommendation_resume.getvalue(), recommendation_resume.name
                    )
                    if db_ok:
                        with SessionLocal() as db:
                            recommendations, model_used = recommend_jobs(
                                resume_text, top_k=top_k, db=db
                            )
                    else:
                        recommendations, model_used = recommend_jobs(
                            resume_text, top_k=top_k, db=None
                        )
                    st.session_state.job_recommendations = recommendations
                    st.session_state.job_model = model_used
            except Exception as exc:
                safe_error(exc)

    recommendations = st.session_state.get("job_recommendations", [])
    if recommendations:
        st.caption(f"Ranking model: {st.session_state.get('job_model')}")
        for rank, job in enumerate(recommendations, 1):
            with st.container(border=True):
                top = st.columns([4, 1])
                top[0].subheader(f"#{rank} {job['title']} — {job['company']}")
                top[1].metric("Fit", f"{job['recommendation_score']:.1f}%")
                st.caption(f"{job['location']} · Source: {job['source']}")
                st.write(job["description"])
                st.write(job["fit_reason"])
                a, b = st.columns(2)
                with a:
                    st.write("**Matched skills**")
                    chips(job["matched_skills"], "matched-chip")
                with b:
                    st.write("**Skill gaps**")
                    chips(job["missing_skills"], "missing-chip")
                if job.get("apply_url") and "example.com" not in job["apply_url"]:
                    st.link_button("Open application page", job["apply_url"])

with history_tab:
    st.caption("Privacy-safe history is isolated to this browser session.")
    records = []
    if not db_ok:
        st.warning("Database is unavailable, so saved history cannot be loaded.")
    else:
        with SessionLocal() as db:
            records = list(
                db.scalars(
                    select(AnalysisRecord)
                    .where(AnalysisRecord.session_id == SESSION_ID)
                    .order_by(AnalysisRecord.created_at.desc())
                    .limit(50)
                )
            )
    if not records:
        st.info("No analyses have been saved in this browser session.")
    else:
        rows = [
            {
                "ID": item.id,
                "Date": format_date(item.created_at),
                "Resume": item.filename,
                "Target role": item.job_title,
                "Overall": round(item.overall_score, 2),
                "Semantic": round(item.semantic_score, 2),
                "Skills": round(item.skill_score, 2),
                "Model": item.model_used.split("/")[-1],
            }
            for item in records
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        selected_id = st.selectbox("Open saved analysis", [item.id for item in records])
        selected = next(item for item in records if item.id == selected_id)
        st.markdown(markdown_report(selected.result))

with recruiter_tab:
    st.markdown("## Recruiter / Admin analytics")
    if not db_ok:
        st.warning("Database is unavailable; analytics cannot be loaded.")
    if settings.admin_dashboard_pin:
        st.text_input("Dashboard PIN", type="password", key="admin_pin")
    if not db_ok:
        pass
    elif not settings.enable_admin_dashboard:
        st.warning("Admin dashboard is disabled by configuration.")
    elif not admin_unlocked():
        st.info("Enter the administrator PIN configured in deployment secrets.")
    else:
        with SessionLocal() as db:
            total = db.scalar(select(func.count(AnalysisRecord.id))) or 0
            avg = db.scalar(select(func.avg(AnalysisRecord.overall_score))) or 0
            high = db.scalar(
                select(func.count(AnalysisRecord.id)).where(AnalysisRecord.overall_score >= 70)
            ) or 0
            jobs_count = db.scalar(
                select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
            ) or 0
            feedback_count = db.scalar(select(func.count(AnalysisFeedback.id))) or 0
            recent = list(
                db.scalars(
                    select(AnalysisRecord)
                    .order_by(AnalysisRecord.created_at.desc())
                    .limit(100)
                )
            )

        metric_cols = st.columns(5)
        metric_cols[0].metric("Total analyses", total)
        metric_cols[1].metric("Average fit", f"{float(avg):.1f}%")
        metric_cols[2].metric("High-fit analyses", high)
        metric_cols[3].metric("Active demo jobs", jobs_count)
        metric_cols[4].metric("Feedback events", feedback_count)

        if recent:
            dashboard_df = pd.DataFrame(
                [
                    {
                        "Date": item.created_at.date().isoformat(),
                        "Target role": item.job_title,
                        "Overall": item.overall_score,
                        "Semantic": item.semantic_score,
                        "Skill coverage": item.skill_score,
                        "Processing ms": item.processing_ms,
                    }
                    for item in recent
                ]
            )
            st.markdown("### Score trend")
            st.line_chart(dashboard_df.set_index("Date")[["Overall", "Semantic", "Skill coverage"]])
            st.markdown("### Role-level summary")
            role_summary = (
                dashboard_df.groupby("Target role")
                .agg(Analyses=("Overall", "count"), Average_fit=("Overall", "mean"))
                .sort_values("Analyses", ascending=False)
                .reset_index()
            )
            st.dataframe(role_summary, use_container_width=True, hide_index=True)
        else:
            st.info("Dashboard data will appear after the first analysis.")

with system_tab:
    st.markdown(
        f"""
        ## Architecture

        **Frontend:** Streamlit recruiter interface  
        **API:** FastAPI with OpenAPI/Swagger documentation  
        **NLP:** `{settings.embedding_model}` Sentence Transformer with TF-IDF fail-safe  
        **Database:** {settings.database_backend} through SQLAlchemy ORM  
        **Deployment:** Streamlit Community Cloud + hosted PostgreSQL, or Docker/Render  

        ### Request pipeline

        1. Validate PDF, DOCX or TXT upload and extract text.
        2. Detect contact details, sections, education, experience dates and a curated skill taxonomy.
        3. Separate required skills from preferred skills in the job description.
        4. Create resume and job-description chunks.
        5. Generate normalized embeddings and calculate requirement-level cosine similarity.
        6. Combine semantic, skill, experience and ATS-quality scores.
        7. Produce explainable evidence, ATS checks and a learning roadmap.
        8. Save a privacy-safe result to PostgreSQL; raw resume text is never persisted.

        ### Database design

        - `analysis_records`: score history, model metadata, processing time and sanitized JSON report.
        - `analysis_feedback`: human feedback for a future model-evaluation loop.
        - `job_postings`: active database-backed role catalog.

        ### Responsible AI

        This system supports recruiter review; it must not automatically reject candidates. Protected personal attributes are not intentional model features, raw resumes are not saved, and human review remains mandatory.
        """
    )
    st.markdown("### API endpoints")
    st.code(
        """GET  /api/v1/health
POST /api/v1/analyze
POST /api/v1/recommend
GET  /api/v1/history?session_id=...
POST /api/v1/history/{id}/feedback
GET  /api/v1/jobs
POST /api/v1/jobs          (admin key)
GET  /api/v1/admin/dashboard (admin key)""",
        language="text",
    )
    st.caption("Run FastAPI locally and open http://localhost:8000/docs for interactive Swagger documentation.")
