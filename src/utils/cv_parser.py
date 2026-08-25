from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pdfplumber

from src.models.student import Student, Skill, SkillLevel, Constraint


TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "go", "rust",
    "react", "reactjs", "react.js", "angular", "vue", "vuejs", "vue.js",
    "next.js", "nextjs", "nuxt", "svelte",
    "node", "nodejs", "node.js", "express",
    "django", "flask", "fastapi", "laravel", "symfony", "spring", "spring boot",
    "html", "css", "sass", "less", "tailwind",
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite", "mariadb",
    "git", "github", "gitlab", "bitbucket",
    "docker", "kubernetes", "k8s", "ci/cd", "jenkins",
    "aws", "azure", "gcp", "heroku", "vercel",
    "linux", "ubuntu", "debian",
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "pandas", "numpy", "opencv", "nlp", "llm",
    "rest", "rest api", "graphql", "api", "websocket",
    "devops", "cloud", "bureautique",
]

DOMAIN_KEYWORDS = {
    "informatique": [
        "informatique", "programmation", "developpement", "logiciel", "web",
        "frontend", "backend", "fullstack", "reseau", "securite", "cloud",
        "developpeur", "application", "fullstack",
    ],
    "mathematiques": [
        "mathematiques", "maths", "algebre", "analyse", "statistiques",
        "probabilites", "geometrie", "optimisation", "modelisation",
    ],
    "physique": [
        "physique", "mecanique", "thermodynamique", "optique",
        "electromagnetisme", "quantique", "chimie",
    ],
    "biologie": [
        "biologie", "bioinformatique", "genetique", "neuroscience",
        "medecine", "sante", "pharmacie", "biotech",
    ],
    "gestion": [
        "gestion", "management", "finance", "comptabilite",
        "entrepreneuriat", "lean", "scrum", "strategie",
    ],
    "marketing": [
        "marketing", "communication", "publicite", "seo",
        "community management", "branding",
    ],
    "design": [
        "design", "ui", "ux", "figma", "sketch",
        "photoshop", "illustrator", "maquettage", "wireframe",
    ],
    "droit": [
        "droit", "juridique", "legal", "contrat", "reglementation",
    ],
    "psychologie": [
        "psychologie", "cognitif", "comportement", "therapie", "coaching",
    ],
}

EDUCATION_PATTERNS = [
    (r"doctorat|phd|docteur|these", "doctorat"),
    (r"master\s*2|m2|mba|mastere|msc|2e.*annee.*master|deuxieme.*annee.*master", "master"),
    (r"master\s*1|m1|magistere|premi[eè]re.*ann[eé]e.*master|1ere.*annee.*master", "bac+4"),
    (r"ing[ée]nieur|diplome d.ing[ée]nieur|ingenieur", "bac+5"),
    (r"licence\s*pro|lp|bachelor", "bac+3"),
    (r"licence|l3|deug|dut|bts|diplome universitaire", "bac+3"),
    (r"bac\+?2|bts|dut|prepa", "bac+2"),
    (r"bac\+?1|l1|premi[èe]re ann[ée]e", "bac+1"),
    (r"bac|baccalaur[ée]at|terminale", "bac"),
]

SKIP_NAME = {
    "profil", "cv", "curriculum", "vitae", "resume", "contact", "contacts",
    "competences", "competence", "formation", "diplomes", "experiences",
    "experience", "centres", "interet", "interets", "loisirs", "reference",
    "references", "langues", "langue", "developpeur fullstack",
    "developpeur fullstack",
}

LEVEL_RANK = {
    "bac": 0, "bac+1": 1, "bac+2": 2, "bac+3": 3, "bac+4": 4,
    "bac+5": 5, "master": 6, "doctorat": 7,
}


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    text_parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        return extract_text_from_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _detect_name(text: str) -> str:
    lines = text.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        lower = stripped.lower()
        if any(skip in lower for skip in SKIP_NAME):
            continue
        if re.match(r"^[\+\d\s\-()]+$", stripped):
            continue
        if "@" in stripped or "http" in lower or "www" in lower or ".com" in lower or ".fr" in lower:
            continue
        if ".vercel" in lower or ".io" in lower or ".app" in lower:
            continue
        if len(stripped) < 3:
            continue
        if re.match(r"^o\s", lower):
            continue
        if re.match(r"^\d", stripped):
            continue

        words = stripped.split()
        if 2 <= len(words) <= 5:
            if all(w[0].isupper() for w in words if len(w) > 2):
                next_lower = lines[i + 1].strip().lower() if i + 1 < len(lines) else ""
                if any(skip in next_lower for skip in SKIP_NAME):
                    continue
                if "@" in lines[i + 1] if i + 1 < len(lines) else False:
                    continue
                if ".vercel" in next_lower or ".com" in next_lower:
                    continue
                return stripped

    for i, line in enumerate(lines[:20]):
        stripped = line.strip()
        lower = stripped.lower()
        if any(skip in lower for skip in SKIP_NAME):
            continue
        if re.match(r"^[\+\d\s\-()]+$", stripped):
            continue
        if "@" in stripped or "http" in lower or ".com" in lower or ".vercel" in lower:
            continue
        if len(stripped) >= 3 and not re.match(r"^o\s", lower) and not re.match(r"^\d", stripped):
            return stripped[:40]

    return "Etudiant"


def _detect_education_level(text: str) -> str:
    text_lower = text.lower()
    best_level = "bac"
    for pattern, level in EDUCATION_PATTERNS:
        if re.search(pattern, text_lower):
            if LEVEL_RANK.get(level, 0) > LEVEL_RANK.get(best_level, 0):
                best_level = level
    return best_level


def _detect_skills(text: str) -> tuple[list[Skill], list[str]]:
    text_lower = text.lower()
    detected: dict[str, SkillLevel] = {}
    found_techs: list[str] = []

    for tech in TECH_SKILLS:
        if tech.lower() in text_lower:
            found_techs.append(tech)
            if "informatique" not in detected:
                detected["informatique"] = SkillLevel.INTERMEDIATE

    skills = []
    for domain, level in detected.items():
        skills.append(Skill(domain=domain, level=level, grade=None))
    return skills, found_techs


LEVEL_ORDER = ["none", "beginner", "intermediate", "advanced", "expert"]


def _detect_interests(text: str) -> list[str]:
    TECH_INTEREST_MAP = {
        "react": "developpement web front-end",
        "reactjs": "developpement web front-end",
        "angular": "developpement web front-end",
        "vue": "developpement web front-end",
        "next.js": "developpement web fullstack",
        "nextjs": "developpement web fullstack",
        "django": "developpement web back-end",
        "flask": "developpement web back-end",
        "fastapi": "developpement web back-end",
        "spring": "developpement web back-end",
        "spring boot": "developpement web back-end",
        "laravel": "developpement web back-end",
        "symfony": "developpement web back-end",
        "node": "developpement web back-end",
        "nodejs": "developpement web back-end",
        "php": "developpement web back-end",
        "python": "programmation python",
        "machine learning": "intelligence artificielle",
        "deep learning": "intelligence artificielle",
        "tensorflow": "intelligence artificielle",
        "pytorch": "intelligence artificielle",
        "nlp": "traitement du langage",
        "sql": "bases de donnees",
        "mysql": "bases de donnees",
        "postgresql": "bases de donnees",
        "mongodb": "bases de donnees",
        "docker": "devops",
        "kubernetes": "devops",
        "git": "developpement logiciel",
        "github": "developpement logiciel",
        "rest api": "development d'API",
        "graphql": "development d'API",
    }

    FRONTEND_KEYWORDS = ["front-end", "frontend", "react", "angular", "vue", "css", "html", "ui", "ux"]
    BACKEND_KEYWORDS = ["back-end", "backend", "spring", "django", "laravel", "php", "node", "api"]
    FULLSTACK_KEYWORDS = ["fullstack", "full-stack", "full stack"]
    AI_KEYWORDS = ["intelligence artificielle", "machine learning", "deep learning", "data science", "ia"]
    DB_KEYWORDS = ["base de donnees", "bases de donnees", "sql", "nosql", "mysql", "postgresql"]

    interests = []

    profil_section = ""
    for line in text.split("\n"):
        lower = line.lower().strip()
        if "profil" in lower and len(lower) < 15:
            idx = text.lower().find(lower)
            profil_section = text[idx:idx+500]
            break

    if profil_section:
        plow = profil_section.lower()
        if any(kw in plow for kw in FULLSTACK_KEYWORDS):
            interests.append("developpement web fullstack")
        elif any(kw in plow for kw in FRONTEND_KEYWORDS) and any(kw in plow for kw in BACKEND_KEYWORDS):
            interests.append("developpement web fullstack")
        elif any(kw in plow for kw in FRONTEND_KEYWORDS):
            interests.append("developpement web front-end")
        elif any(kw in plow for kw in BACKEND_KEYWORDS):
            interests.append("developpement web back-end")

        if any(kw in plow for kw in AI_KEYWORDS):
            interests.append("intelligence artificielle")
        if any(kw in plow for kw in DB_KEYWORDS):
            interests.append("bases de donnees")

    all_techs = re.findall(r"o\s+(.+?)(?:\n|$)", text, re.IGNORECASE)
    for tech_line in all_techs:
        tech_clean = re.sub(r"[^a-zA-Z\s\+\#]", "", tech_line).strip().lower()
        for tech_key, interest in TECH_INTEREST_MAP.items():
            if tech_key in tech_clean:
                if interest not in interests:
                    interests.append(interest)

    lines = text.split("\n")
    in_section = False
    for line in lines:
        lower = line.lower().strip()
        if "centres d'int" in lower or "centre d'int" in lower:
            in_section = True
            continue
        if in_section:
            if re.match(r"^[A-Z]{4,}", line.strip()):
                break
            if re.match(r"^o\s", line.strip(), re.IGNORECASE):
                item = re.sub(r"^[oO]\s+", "", line).strip()
                item = re.sub(r"[^a-zA-Z\s\-]", "", item).strip()
                item = re.sub(r"\s+", " ", item)
                if 2 < len(item) < 40:
                    li = item.lower()
                    if li not in interests:
                        interests.append(li)

    seen = set()
    unique = []
    for i in interests:
        if i not in seen:
            seen.add(i)
            unique.append(i)
    return unique[:10]


def parse_cv(pdf_path: str | Path | None = None, pdf_bytes: bytes | None = None) -> Student:
    if pdf_bytes:
        text = extract_text_from_bytes(pdf_bytes)
    elif pdf_path:
        text = extract_text_from_pdf(pdf_path)
    else:
        raise ValueError("Il faut fournir pdf_path ou pdf_bytes")

    if not text.strip():
        return Student(
            id="cv_import",
            name="Etudiant (CV)",
            current_level="bac+3",
            skills=[],
            interests=[],
            constraints=Constraint(),
            free_text="CV vide ou illisible",
        )

    name = _detect_name(text)
    level = _detect_education_level(text)
    skills, found_techs = _detect_skills(text)
    interests = _detect_interests(text)

    techs_str = ", ".join(sorted(set(found_techs))) if found_techs else ""
    free_text = f"Extrait du CV ({len(text)} caracteres)"
    if techs_str:
        free_text += f" | Technologies detectees : {techs_str}"

    return Student(
        id="cv_import",
        name=name,
        current_level=level,
        skills=skills,
        interests=interests,
        constraints=Constraint(),
        free_text=free_text,
    )
