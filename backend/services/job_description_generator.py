"""Universal job-description generation with an optional Gemini AI provider.

The online provider is optional. When no API key is configured, or the provider
is unavailable, the application produces a deterministic role-family draft so
the core resume-analysis workflow remains usable.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

from backend.config import settings


@dataclass(frozen=True)
class GeneratedJobDescription:
    text: str
    source: str
    warning: str | None = None


COMMON_REQUIRED = [
    "Communication",
    "Problem Solving",
    "Teamwork",
    "Documentation",
    "Time Management",
]

ROLE_FAMILIES: list[dict[str, object]] = [
    {
        "name": "software engineering",
        "keywords": (
            "software", "developer", "programmer", "frontend", "front end",
            "backend", "back end", "full stack", "fullstack", "web developer",
            "mobile developer", "android", "ios", "java developer", "python developer",
            "dotnet", ".net", "qa engineer", "test engineer",
        ),
        "responsibilities": [
            "Design, implement and test maintainable software features from clear requirements.",
            "Review code, diagnose defects and improve reliability, security and performance.",
            "Integrate APIs, databases or third-party services with validation and error handling.",
            "Use version control, automated tests and documentation to support team delivery.",
            "Collaborate with product, design and engineering stakeholders throughout delivery.",
        ],
        "required": [
            "Programming", "Object-Oriented Programming", "Data Structures", "Algorithms",
            "Git", "Testing", "Debugging", "APIs", "Databases",
        ],
        "preferred": ["Cloud Platforms", "Docker", "CI/CD", "Agile", "System Design"],
        "education": "A degree or diploma in Computer Science, IT or a related field, or equivalent practical project experience.",
    },
    {
        "name": "data and artificial intelligence",
        "keywords": (
            "data analyst", "business analyst", "data scientist", "data engineer",
            "machine learning", "ml engineer", "artificial intelligence", " ai ",
            "nlp", "computer vision", "bi analyst", "analytics",
        ),
        "responsibilities": [
            "Collect, clean and validate data from relevant sources.",
            "Perform analysis or build models using appropriate methods and evaluation metrics.",
            "Create reproducible workflows, visualizations and clear decision-ready findings.",
            "Document assumptions, data quality limitations and experiment results.",
            "Collaborate with technical and business stakeholders to translate needs into solutions.",
        ],
        "required": [
            "Data Analysis", "Statistics", "SQL", "Data Visualization", "Python",
            "Data Cleaning", "Analytical Thinking", "Excel",
        ],
        "preferred": ["Machine Learning", "Pandas", "Power BI", "Tableau", "Cloud Platforms"],
        "education": "A degree in Computer Science, Data Science, Mathematics, Statistics, Engineering or a related field, or equivalent applied experience.",
    },
    {
        "name": "cybersecurity and infrastructure",
        "keywords": (
            "cyber", "security analyst", "soc analyst", "penetration", "network engineer",
            "network administrator", "system administrator", "devops", "site reliability",
            "sre", "cloud engineer", "infrastructure",
        ),
        "responsibilities": [
            "Monitor systems, investigate incidents and document technical findings.",
            "Apply secure configuration, access-control and risk-management practices.",
            "Automate repeatable operational tasks and improve service reliability.",
            "Support vulnerability remediation, backup, recovery and change management.",
            "Collaborate with engineering and business teams to reduce operational risk.",
        ],
        "required": [
            "Linux", "Computer Networks", "Troubleshooting", "Security Fundamentals",
            "Scripting", "Monitoring", "Incident Management", "Documentation",
        ],
        "preferred": ["Cloud Security", "Docker", "SIEM", "CI/CD", "Infrastructure as Code"],
        "education": "A degree, diploma or certification in Computer Science, IT, Networking or Cybersecurity, or equivalent hands-on lab experience.",
    },
    {
        "name": "design and creative",
        "keywords": (
            "ui designer", "ux designer", "graphic designer", "product designer",
            "visual designer", "illustrator", "animator", "video editor", "photographer",
            "creative designer", "content designer",
        ),
        "responsibilities": [
            "Translate briefs and user needs into clear, consistent visual or interaction concepts.",
            "Create drafts, prototypes or production assets and iterate from feedback.",
            "Maintain brand, accessibility and quality standards across deliverables.",
            "Present design decisions and collaborate with product, marketing or engineering teams.",
            "Organize source files, versions and reusable design components.",
        ],
        "required": [
            "Design Principles", "Visual Communication", "Creativity", "Prototyping",
            "Attention to Detail", "Portfolio", "Stakeholder Communication",
        ],
        "preferred": ["Figma", "Adobe Creative Suite", "User Research", "Accessibility", "Motion Design"],
        "education": "A degree or diploma in Design, Fine Arts, Media or a related field, or a strong role-relevant portfolio.",
    },
    {
        "name": "marketing and communications",
        "keywords": (
            "marketing", "seo", "social media", "content writer", "copywriter",
            "communications", "brand", "public relations", "pr executive", "growth",
            "digital marketing", "content strategist",
        ),
        "responsibilities": [
            "Plan and execute audience-focused campaigns or communication activities.",
            "Create, edit and publish accurate content across appropriate channels.",
            "Track performance metrics and recommend data-informed improvements.",
            "Coordinate calendars, assets and approvals with internal and external stakeholders.",
            "Maintain consistent brand voice, quality and compliance standards.",
        ],
        "required": [
            "Content Creation", "Written Communication", "Campaign Management",
            "Market Research", "Analytics", "Audience Understanding", "Editing",
        ],
        "preferred": ["SEO", "Social Media Management", "Google Analytics", "Email Marketing", "Graphic Design"],
        "education": "A degree in Marketing, Communications, Business, Journalism or a related field, or a relevant portfolio and campaign experience.",
    },
    {
        "name": "sales and business development",
        "keywords": (
            "sales", "business development", "account executive", "relationship manager",
            "inside sales", "field sales", "sales representative", "key account",
            "partnerships", "pre sales", "presales",
        ),
        "responsibilities": [
            "Identify and qualify prospective customers or partnership opportunities.",
            "Understand customer needs and present suitable products or solutions.",
            "Maintain accurate pipeline, activity and forecast records.",
            "Negotiate next steps and coordinate handoffs with delivery or support teams.",
            "Build trusted relationships and work toward agreed revenue or growth targets.",
        ],
        "required": [
            "Sales", "Lead Generation", "Negotiation", "Customer Relationship Management",
            "Presentation", "Communication", "Target Orientation",
        ],
        "preferred": ["CRM Software", "Market Research", "B2B Sales", "Account Management", "Excel"],
        "education": "A degree in Business, Marketing or a related field is useful; demonstrated sales ability and customer-facing experience may be accepted instead.",
    },
    {
        "name": "human resources",
        "keywords": (
            "human resources", " hr ", "recruiter", "talent acquisition", "people operations",
            "hr generalist", "payroll", "learning and development", "l&d",
        ),
        "responsibilities": [
            "Support recruitment, onboarding, employee records or people-program operations.",
            "Coordinate communication with candidates, employees and hiring stakeholders.",
            "Maintain accurate confidential data and follow employment policies.",
            "Prepare reports, schedules and documentation for recurring HR processes.",
            "Contribute to a fair, respectful and consistent employee experience.",
        ],
        "required": [
            "Human Resources", "Recruitment", "Interview Coordination", "Confidentiality",
            "Employee Communication", "Record Management", "Organization",
        ],
        "preferred": ["HRIS", "Labor Law Awareness", "Payroll", "Excel", "Onboarding"],
        "education": "A degree in Human Resources, Business, Psychology or a related field, or equivalent people-operations experience.",
    },
    {
        "name": "finance and accounting",
        "keywords": (
            "accountant", "accounting", "finance analyst", "financial analyst", "auditor",
            "tax", "bookkeeper", "investment analyst", "credit analyst", "banking",
            "chartered accountant", "ca intern",
        ),
        "responsibilities": [
            "Prepare, validate and reconcile financial records or analytical reports.",
            "Investigate variances and maintain supporting documentation and controls.",
            "Apply relevant accounting, tax, audit or financial-analysis standards.",
            "Communicate findings clearly to internal stakeholders.",
            "Protect confidential information and meet reporting deadlines.",
        ],
        "required": [
            "Accounting", "Financial Analysis", "Excel", "Reconciliation", "Attention to Detail",
            "Financial Reporting", "Numerical Accuracy",
        ],
        "preferred": ["Tally", "ERP Systems", "Taxation", "Power BI", "Audit"],
        "education": "A degree in Commerce, Accounting, Finance, Economics or a related field; role-specific professional study may be preferred.",
    },
    {
        "name": "healthcare",
        "keywords": (
            "nurse", "doctor", "physician", "medical", "pharmacist", "physiotherapist",
            "dentist", "clinical", "lab technician", "radiologist", "healthcare",
            "caregiver", "nutritionist",
        ),
        "responsibilities": [
            "Deliver safe, respectful and evidence-based care within the role's authorized scope.",
            "Assess needs, maintain accurate records and communicate changes promptly.",
            "Follow hygiene, privacy, medication, equipment and escalation procedures.",
            "Coordinate with patients, families and multidisciplinary care teams.",
            "Maintain required registration, training and professional standards.",
        ],
        "required": [
            "Patient Care", "Clinical Documentation", "Communication", "Safety Procedures",
            "Confidentiality", "Teamwork", "Attention to Detail",
        ],
        "preferred": ["Electronic Health Records", "Emergency Response", "Patient Education", "Quality Improvement"],
        "education": "The legally required healthcare qualification, registration or license for the role and location is mandatory.",
    },
    {
        "name": "education and training",
        "keywords": (
            "teacher", "professor", "lecturer", "tutor", "trainer", "faculty",
            "instructional designer", "academic counselor", "school counselor", "educator",
        ),
        "responsibilities": [
            "Plan and deliver clear learning activities aligned with defined outcomes.",
            "Assess progress, provide constructive feedback and maintain accurate records.",
            "Adapt instruction for learner needs and create an inclusive environment.",
            "Communicate with learners, colleagues and relevant guardians or stakeholders.",
            "Maintain subject knowledge and follow institutional policies.",
        ],
        "required": [
            "Teaching", "Lesson Planning", "Subject Knowledge", "Assessment",
            "Classroom Management", "Communication", "Student Support",
        ],
        "preferred": ["Educational Technology", "Curriculum Design", "Learning Management Systems", "Counseling"],
        "education": "The required subject qualification and teaching credential for the institution and location, or equivalent training experience.",
    },
    {
        "name": "legal and compliance",
        "keywords": (
            "lawyer", "legal", "paralegal", "compliance", "company secretary",
            "contract analyst", "risk analyst", "legal counsel", "advocate",
        ),
        "responsibilities": [
            "Research relevant laws, regulations, policies or contractual requirements.",
            "Draft, review and organize accurate documents and case or compliance records.",
            "Identify risks, exceptions and required approvals.",
            "Communicate findings clearly while protecting confidential information.",
            "Track deadlines and support audits, filings or dispute-resolution processes.",
        ],
        "required": [
            "Legal Research", "Document Review", "Compliance", "Confidentiality",
            "Analytical Thinking", "Written Communication", "Attention to Detail",
        ],
        "preferred": ["Contract Drafting", "Regulatory Reporting", "Risk Management", "Case Management"],
        "education": "The applicable law, compliance or governance qualification for the role; regulated legal practice requires appropriate authorization.",
    },
    {
        "name": "product, project and operations management",
        "keywords": (
            "product manager", "project manager", "program manager", "operations manager",
            "operations executive", "product owner", "scrum master", "coordinator",
            "management trainee", "process analyst",
        ),
        "responsibilities": [
            "Define objectives, scope, priorities and measurable success criteria.",
            "Coordinate plans, owners, risks, dependencies and stakeholder communication.",
            "Track delivery and use data to identify issues and improvement opportunities.",
            "Document decisions, processes and action items.",
            "Support cross-functional teams in delivering reliable customer or business outcomes.",
        ],
        "required": [
            "Project Management", "Stakeholder Management", "Planning", "Risk Management",
            "Process Improvement", "Communication", "Data Analysis",
        ],
        "preferred": ["Agile", "Scrum", "Jira", "Product Analytics", "Budget Management"],
        "education": "A degree in Business, Engineering, Management or a role-relevant discipline, or equivalent delivery experience.",
    },
    {
        "name": "supply chain and logistics",
        "keywords": (
            "supply chain", "logistics", "warehouse", "procurement", "purchase executive",
            "inventory", "transport coordinator", "shipping", "fleet", "demand planner",
        ),
        "responsibilities": [
            "Coordinate the timely movement, purchase, storage or availability of goods.",
            "Maintain accurate inventory, order and supplier records.",
            "Monitor cost, quality, service and delivery performance.",
            "Resolve operational exceptions and communicate with vendors and internal teams.",
            "Follow safety, documentation and regulatory requirements.",
        ],
        "required": [
            "Supply Chain", "Logistics", "Inventory Management", "Vendor Coordination",
            "Excel", "Planning", "Record Accuracy",
        ],
        "preferred": ["ERP Systems", "Procurement", "Demand Forecasting", "Warehouse Management Systems", "Data Analysis"],
        "education": "A degree or diploma in Supply Chain, Logistics, Operations, Business or a related discipline, or equivalent operational experience.",
    },
    {
        "name": "customer service and hospitality",
        "keywords": (
            "customer support", "customer service", "support executive", "call center",
            "customer success", "hotel", "hospitality", "front desk", "receptionist",
            "restaurant", "retail associate", "store associate",
        ),
        "responsibilities": [
            "Respond to customer requests accurately, respectfully and within service standards.",
            "Understand needs, resolve common issues and escalate complex cases appropriately.",
            "Maintain complete interaction, booking, order or service records.",
            "Coordinate with internal teams to deliver a consistent customer experience.",
            "Follow privacy, payment, safety and quality procedures.",
        ],
        "required": [
            "Customer Service", "Communication", "Problem Resolution", "Active Listening",
            "Record Management", "Professionalism", "Teamwork",
        ],
        "preferred": ["CRM Software", "Multilingual Communication", "Sales", "Hospitality Operations", "Conflict Resolution"],
        "education": "A relevant diploma or degree may be useful; strong customer-facing experience and communication skills are often accepted.",
    },
    {
        "name": "engineering and manufacturing",
        "keywords": (
            "mechanical engineer", "electrical engineer", "civil engineer", "electronics engineer",
            "chemical engineer", "manufacturing engineer", "production engineer", "quality engineer",
            "maintenance engineer", "automobile engineer", "industrial engineer",
        ),
        "responsibilities": [
            "Apply engineering principles to design, analyze, test or improve systems and processes.",
            "Prepare calculations, drawings, specifications or technical records.",
            "Investigate failures and support corrective and preventive actions.",
            "Coordinate with production, quality, suppliers and project stakeholders.",
            "Follow applicable safety, quality and regulatory standards.",
        ],
        "required": [
            "Engineering Fundamentals", "Technical Drawing", "Problem Solving", "Quality Standards",
            "Safety", "Data Analysis", "Technical Documentation",
        ],
        "preferred": ["CAD", "Simulation", "Lean Manufacturing", "Project Management", "Industry Standards"],
        "education": "A degree or diploma in the relevant engineering discipline; regulated responsibilities may require professional authorization.",
    },
    {
        "name": "culinary and food service",
        "keywords": (
            "chef", "cook", "baker", "pastry", "kitchen", "food production",
            "culinary", "restaurant manager", "catering",
        ),
        "responsibilities": [
            "Prepare and present food consistently according to recipes, quality standards and service timelines.",
            "Maintain food safety, hygiene, storage and allergen-control procedures.",
            "Plan preparation work, control waste and monitor stock availability.",
            "Coordinate with kitchen and service teams during busy operations.",
            "Keep work areas, equipment and production records organized.",
        ],
        "required": [
            "Food Preparation", "Food Safety", "Kitchen Operations", "Hygiene Standards",
            "Time Management", "Teamwork", "Attention to Detail",
        ],
        "preferred": ["Menu Planning", "Inventory Control", "Cost Control", "Allergen Awareness", "Culinary Certification"],
        "education": "A culinary qualification or equivalent supervised kitchen experience; locally required food-safety certification may be mandatory.",
    },
    {
        "name": "aviation and safety-critical transport",
        "keywords": (
            "pilot", "flight attendant", "cabin crew", "air traffic controller",
            "airport operations", "aviation", "dispatcher", "railway controller",
            "train driver", "marine officer", "ship officer",
        ),
        "responsibilities": [
            "Perform role duties in strict accordance with operational and safety procedures.",
            "Monitor changing conditions, communicate clearly and make timely decisions.",
            "Maintain accurate logs, checklists and regulatory records.",
            "Coordinate with control, crew, maintenance and emergency stakeholders.",
            "Complete recurrent training and remain fit for authorized duty.",
        ],
        "required": [
            "Safety Procedures", "Situational Awareness", "Clear Communication", "Decision Making",
            "Operational Discipline", "Record Keeping", "Stress Management",
        ],
        "preferred": ["Emergency Response", "Navigation", "Meteorology", "Human Factors", "Operations Control"],
        "education": "The legally required aviation, maritime or transport qualification, medical fitness and operating license for the exact role and jurisdiction are mandatory.",
    },
    {
        "name": "construction and skilled trades",
        "keywords": (
            "electrician", "plumber", "carpenter", "welder", "mason", "mechanic",
            "hvac", "construction worker", "site supervisor", "maintenance technician",
            "machine operator", "fitter", "technician",
        ),
        "responsibilities": [
            "Complete installation, repair, fabrication or maintenance work from approved instructions.",
            "Inspect tools, materials and work areas before and after each task.",
            "Diagnose faults and perform safe corrective work within authorized scope.",
            "Record completed work, measurements, parts and outstanding risks.",
            "Follow site safety, permit, quality and housekeeping procedures.",
        ],
        "required": [
            "Trade Skills", "Safety Procedures", "Technical Drawings", "Hand and Power Tools",
            "Troubleshooting", "Measurement", "Quality Standards",
        ],
        "preferred": ["Preventive Maintenance", "Equipment Inspection", "Work Permits", "Inventory Control", "Trade Certification"],
        "education": "A relevant trade certificate, apprenticeship or documented practical experience; regulated work requires the applicable local license.",
    },
    {
        "name": "agriculture and environment",
        "keywords": (
            "farmer", "agriculture", "agronomist", "horticulture", "forestry",
            "environmental", "sustainability", "conservation", "farm manager",
            "veterinary assistant",
        ),
        "responsibilities": [
            "Monitor field, crop, animal or environmental conditions and maintain accurate observations.",
            "Apply approved production, conservation, safety and biosecurity practices.",
            "Plan resources, schedules and preventive actions based on seasonal needs.",
            "Use data and field evidence to identify risks and improve outcomes.",
            "Coordinate with workers, suppliers, communities or regulatory stakeholders.",
        ],
        "required": [
            "Field Operations", "Environmental Awareness", "Record Keeping", "Safety",
            "Observation", "Planning", "Problem Solving",
        ],
        "preferred": ["GIS", "Sustainable Practices", "Equipment Operation", "Data Analysis", "Regulatory Compliance"],
        "education": "A role-relevant agriculture, environmental science or vocational qualification, or equivalent field experience.",
    },
    {
        "name": "public safety and social services",
        "keywords": (
            "social worker", "counselor", "community worker", "police", "firefighter",
            "emergency responder", "case worker", "public administration", "civil services",
        ),
        "responsibilities": [
            "Assess situations, follow approved procedures and protect the safety and dignity of people served.",
            "Maintain accurate confidential records and communicate material changes promptly.",
            "Coordinate referrals, response actions or services with relevant agencies and teams.",
            "Apply de-escalation, safeguarding and ethical decision-making principles.",
            "Participate in training, supervision and continuous service improvement.",
        ],
        "required": [
            "Public Service", "Communication", "Ethical Judgment", "Record Keeping",
            "Crisis Response", "Confidentiality", "Teamwork",
        ],
        "preferred": ["Case Management", "Safeguarding", "Community Outreach", "First Aid", "Conflict Resolution"],
        "education": "The qualification, background checks, physical standards or professional registration legally required for the exact public-service role are mandatory.",
    },
    {
        "name": "research and laboratory",
        "keywords": (
            "research assistant", "researcher", "scientist", "laboratory", "lab assistant",
            "chemist", "biologist", "microbiologist", "research analyst",
        ),
        "responsibilities": [
            "Conduct literature review, experiments, observations or structured data collection.",
            "Follow approved protocols and maintain accurate, traceable records.",
            "Analyze results, identify limitations and communicate findings.",
            "Maintain equipment, samples, data and safety requirements.",
            "Collaborate with supervisors and project partners on research milestones.",
        ],
        "required": [
            "Research Methods", "Data Collection", "Data Analysis", "Scientific Writing",
            "Laboratory Safety", "Attention to Detail", "Documentation",
        ],
        "preferred": ["Statistical Software", "Literature Review", "Experimental Design", "Publication Support"],
        "education": "A degree in the relevant scientific discipline; specialized laboratory roles may require additional certification or postgraduate study.",
    },
]


def _normalize_title(title: str) -> str:
    return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#./& -]", " ", title.lower())).strip() + " "


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = re.sub(r"\s+", " ", item).strip(" .,-")
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _infer_seniority(title: str, selected: str | None = None) -> str:
    if selected and selected.lower() != "auto-detect":
        return selected
    lower = title.lower()
    if any(word in lower for word in ("intern", "trainee", "apprentice")):
        return "Intern / Trainee"
    if any(word in lower for word in ("junior", "associate", "entry level")):
        return "Entry level"
    if any(word in lower for word in ("lead", "principal", "staff", "architect")):
        return "Lead / Principal"
    if any(word in lower for word in ("manager", "head", "director", "vp", "vice president")):
        return "Manager / Leadership"
    if "senior" in lower or "sr." in lower or "sr " in lower:
        return "Senior"
    return "Mid level"


def _select_family(title: str) -> dict[str, object] | None:
    normalized = _normalize_title(title)
    scored: list[tuple[int, int, dict[str, object]]] = []
    for index, family in enumerate(ROLE_FAMILIES):
        score = 0
        for keyword in family["keywords"]:  # type: ignore[index]
            key = _normalize_title(str(keyword)).strip()
            if key and f" {key} " in normalized:
                score += max(1, len(key.split()))
        if score:
            scored.append((score, -index, family))
    return max(scored, default=(0, 0, None), key=lambda item: (item[0], item[1]))[2]


def _fallback_description(
    title: str,
    seniority: str | None = None,
    employment_type: str = "Full-time",
    location: str = "Not specified",
) -> GeneratedJobDescription:
    safe_title = re.sub(r"[\r\n]+", " ", title).strip() or "General Professional"
    resolved_seniority = _infer_seniority(safe_title, seniority)
    family = _select_family(safe_title)

    if family is None:
        family_name = "general professional"
        responsibilities = [
            f"Perform the core day-to-day responsibilities normally associated with a {safe_title} role.",
            "Understand requirements, plan work and deliver accurate outcomes within agreed timelines.",
            "Communicate progress, risks and decisions clearly to relevant stakeholders.",
            "Maintain complete records and follow applicable quality, safety and confidentiality standards.",
            "Continuously improve role knowledge, processes and service quality.",
        ]
        required = [
            "Role-Specific Knowledge", "Communication", "Problem Solving", "Attention to Detail",
            "Time Management", "Teamwork", "Documentation",
        ]
        preferred = ["Relevant Tools", "Industry Knowledge", "Customer or Stakeholder Management", "Process Improvement"]
        education = "A role-relevant qualification, certification or demonstrable practical experience. Any legally required license remains mandatory."
        warning = "The title was not mapped to a known role family, so a general professional draft was created. Review and edit it before analysis."
    else:
        family_name = str(family["name"])
        responsibilities = list(family["responsibilities"])  # type: ignore[arg-type]
        required = _unique(list(family["required"]) + COMMON_REQUIRED)  # type: ignore[arg-type]
        preferred = _unique(list(family["preferred"]))  # type: ignore[arg-type]
        education = str(family["education"])
        warning = None

    if resolved_seniority == "Intern / Trainee":
        experience = "No formal experience is required; strong coursework, projects, volunteering or supervised practical work may be accepted."
    elif resolved_seniority == "Entry level":
        experience = "Approximately 0–2 years of relevant experience, internships or strong practical projects are suitable."
    elif resolved_seniority == "Senior":
        experience = "Several years of directly relevant experience with evidence of independent delivery and mentoring are expected."
    elif resolved_seniority == "Lead / Principal":
        experience = "Extensive specialist experience, architecture or technical leadership, and cross-team influence are expected."
    elif resolved_seniority == "Manager / Leadership":
        experience = "Relevant domain experience plus ownership of people, budgets, delivery, operations or strategy is expected."
    else:
        experience = "Relevant practical experience demonstrating reliable independent delivery is preferred."

    lines = [
        safe_title,
        "",
        "Role summary",
        f"This is a generated benchmark description for a {resolved_seniority.lower()} {safe_title} role in the {family_name} family. It is intended for resume analysis and should be reviewed before real hiring use.",
        "",
        "Employment details",
        f"- Employment type: {employment_type}",
        f"- Location: {location}",
        f"- Seniority: {resolved_seniority}",
        "",
        "Responsibilities",
        *[f"- {item}" for item in responsibilities],
        "",
        "Required skills",
        *[f"- {item}" for item in required[:12]],
        "",
        "Preferred skills",
        *[f"- {item}" for item in preferred[:8]],
        "",
        "Education and experience",
        f"- {education}",
        f"- {experience}",
    ]
    return GeneratedJobDescription("\n".join(lines).strip(), "Built-in universal fallback", warning)


def _gemini_prompt(title: str, seniority: str, employment_type: str, location: str) -> str:
    return f"""Create a realistic, neutral benchmark job description for resume matching.

Job title: {title}
Seniority: {seniority}
Employment type: {employment_type}
Location/context: {location}

Rules:
- Infer the commonly understood occupation from the title, including non-technical roles.
- Do not invent a company, salary, benefits, legal promises, protected-characteristic preferences, or claims about a specific employer.
- For licensed or regulated occupations, clearly state that the legally required local qualification or license is mandatory.
- Use concise professional English and this exact plain-text structure:

{{job title}}

Role summary
{{2-3 sentences}}

Employment details
- Employment type: ...
- Location: ...
- Seniority: ...

Responsibilities
- {{6 specific bullets}}

Required skills
- {{8-12 short, concrete skill phrases; one skill per bullet}}

Preferred skills
- {{4-7 short, concrete skill phrases; one skill per bullet}}

Education and experience
- {{2-3 realistic bullets}}

- Keep each skill phrase under six words where possible because another component parses these bullets.
- Output only the job description, with no markdown fences and no extra commentary.
"""


def _generate_with_gemini(
    title: str,
    seniority: str,
    employment_type: str,
    location: str,
) -> str:
    model = settings.gemini_model.strip() or "gemini-3.6-flash"
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="-._")
        + ":generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": _gemini_prompt(title, seniority, employment_type, location)}]}],
        "generationConfig": {
            "maxOutputTokens": 1400,
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=settings.gemini_timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    candidates = body.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidate text.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(str(part.get("text", "")) for part in parts).strip()
    text = re.sub(r"^```(?:text|markdown)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    if len(text) < 180 or "Required skills" not in text or "Responsibilities" not in text:
        raise RuntimeError("Gemini response did not follow the requested job-description structure.")
    return text


def generate_job_description(
    title: str,
    seniority: str | None = None,
    employment_type: str = "Full-time",
    location: str = "Not specified",
) -> GeneratedJobDescription:
    """Generate a JD using Gemini when configured, otherwise use local fallback."""
    safe_title = re.sub(r"[\r\n]+", " ", title).strip()
    if len(safe_title) < 2:
        raise ValueError("Enter a meaningful job title first.")
    resolved_seniority = _infer_seniority(safe_title, seniority)

    if settings.gemini_api_key:
        try:
            text = _generate_with_gemini(
                safe_title,
                resolved_seniority,
                employment_type,
                location,
            )
            return GeneratedJobDescription(text, f"Gemini AI ({settings.gemini_model})")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            fallback = _fallback_description(
                safe_title, resolved_seniority, employment_type, location
            )
            return GeneratedJobDescription(
                fallback.text,
                fallback.source,
                f"AI generation was unavailable, so the local fallback was used: {exc}",
            )

    return _fallback_description(safe_title, resolved_seniority, employment_type, location)
