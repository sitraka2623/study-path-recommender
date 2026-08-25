import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.models.student import Student, Skill, SkillLevel, Constraint
from src.engines.hybrid import HybridEngine
from src.engines.rule_engine import RuleEngine
from src.engines.llm_engine import LLMEngine
from src.knowledge.loader import load_programs, load_students
from src.utils.cv_parser import parse_cv

# ── Style personnalisé ──────────────────────────────────────────────
st.set_page_config(page_title="Orientation IA", page_icon="🎓", layout="wide")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #7eb8da;
    --primary-light: #a8d4f0;
    --accent: #f0a050;
    --accent-hover: #e08a30;
    --bg: #0f1923;
    --bg-secondary: #162230;
    --card-bg: #1a2d3d;
    --card-bg-hover: #1f3448;
    --text: #e8edf2;
    --text-muted: #7a8fa0;
    --border: #2a3f52;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #f87171;
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
    --radius: 10px;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
}

[data-testid="stHeader"] { background: var(--bg) !important; }
[data-testid="stToolbar"] { background: var(--bg) !important; }

section[data-testid="stSidebar"] {
    background: #0a1219 !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text) !important;
}

h1 { color: var(--primary-light) !important; font-weight: 700 !important; }
h2 { color: var(--primary) !important; font-weight: 600 !important; }
h3 { color: var(--text) !important; font-weight: 600 !important; }
p, li, span, label, div { color: var(--text) !important; }

div[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow);
}
div[data-testid="stMetric"] label { color: var(--text-muted) !important; font-weight: 500 !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: var(--accent) !important; font-weight: 700 !important; }

div[data-testid="stTabs"] {
    background: transparent;
}
div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    padding: 10px 20px;
    border-radius: 8px 8px 0 0;
    background: var(--bg-secondary);
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-bottom: none;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: var(--card-bg);
    color: var(--primary-light);
    border-color: var(--primary);
    border-bottom: 2px solid var(--card-bg);
}
div[data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--text);
}

div[data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
}

div[data-baseweb="tab-highlight"] {
    background: var(--accent) !important;
}

div[data-baseweb="input"] {
    border-radius: 8px !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    border: none !important;
    color: #0f1923 !important;
    box-shadow: var(--shadow-md) !important;
}
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 6px 20px rgba(240,160,80,0.3) !important;
    transform: translateY(-1px);
}

div[data-baseweb="select"] {
    border-radius: 8px !important;
}

div[data-baseweb="expander"] {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    background: var(--card-bg);
}
div[data-baseweb="expander"] summary {
    background: var(--card-bg);
    color: var(--text);
    padding: 14px 18px;
}
div[data-baseweb="expander"]:hover {
    border-color: var(--primary);
}

.stDataFrame {
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
}

.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 30px;
    background: linear-gradient(135deg, #0a1219 0%, #162230 50%, #1a2d3d 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 28px;
    box-shadow: var(--shadow-md);
}
.header-bar h1 {
    color: var(--primary-light) !important;
    font-size: 1.6rem !important;
    margin: 0 !important;
}
.header-bar p {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin: 4px 0 0 0;
}
.header-badge {
    background: rgba(240,160,80,0.15);
    color: var(--accent);
    border: 1px solid rgba(240,160,80,0.3);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.profile-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
}
.profile-card h4 {
    margin: 0 0 8px 0;
    color: var(--primary);
    font-size: 1rem;
    font-weight: 600;
}
.profile-card p {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 1.5;
}

.rec-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 26px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
    border-left: 4px solid var(--accent);
    transition: box-shadow 0.2s;
}
.rec-card:hover {
    box-shadow: var(--shadow-md);
}
.rec-card.top { border-left-color: var(--success); }
.rec-card.warn { border-left-color: var(--warning); }

.score-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    color: white;
}
.score-badge.high { background: var(--success); }
.score-badge.mid { background: var(--warning); }
.score-badge.low { background: var(--danger); }

.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
}
.tag.domain { background: rgba(126,184,218,0.15); color: var(--primary-light); border: 1px solid rgba(126,184,218,0.3); }
.tag.cost { background: rgba(240,160,80,0.15); color: var(--accent); border: 1px solid rgba(240,160,80,0.3); }
.tag.duration { background: rgba(52,211,153,0.15); color: var(--success); border: 1px solid rgba(52,211,153,0.3); }
.tag.location { background: rgba(168,212,240,0.15); color: var(--primary-light); border: 1px solid rgba(168,212,240,0.3); }

.uncertainty-section {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.3);
    border-radius: var(--radius);
    padding: 18px 22px;
    margin-bottom: 18px;
}
.uncertainty-section h4 { color: var(--warning); margin: 0 0 10px 0; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Données ─────────────────────────────────────────────────────────
@st.cache_data
def get_programs():
    return load_programs()

@st.cache_data
def get_sample_students():
    return load_students()

PROGRAMS = get_programs()
SAMPLE_STUDENTS = get_sample_students()


# ── Construction du formulaire ──────────────────────────────────────
def build_student_from_form() -> Student:
    st.markdown("<h3 style='margin-top:0'>Informations personnelles</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Nom complet", value="Étudiant")
    with c2:
        level = st.selectbox(
            "Niveau d'études actuel",
            ["bac", "bac+1", "bac+2", "bac+3", "bac+4", "bac+5", "master", "doctorat"],
            index=3,
        )

    st.markdown("<h3>Compétences académiques</h3>", unsafe_allow_html=True)
    skills = []
    cols = st.columns(3)
    domains = [
        ("informatique", "Informatique"), ("mathematiques", "Mathématiques"),
        ("physique", "Physique"), ("biologie", "Biologie"),
        ("gestion", "Gestion"), ("marketing", "Marketing"),
        ("design", "Design"), ("droit", "Droit"), ("psychologie", "Psychologie"),
    ]
    for i, (key, label) in enumerate(domains):
        with cols[i % 3]:
            has = st.checkbox(label, key=f"skill_{key}")
            if has:
                lvl = st.selectbox(
                    f"Niveau", ["beginner", "intermediate", "advanced", "expert"],
                    key=f"lvl_{key}", format_func=lambda x: {
                        "beginner": "Débutant", "intermediate": "Intermédiaire",
                        "advanced": "Avancé", "expert": "Expert"
                    }.get(x, x),
                )
                grade = st.number_input(f"Note /20", 0.0, 20.0, 12.0, 0.5, key=f"grade_{key}")
                skills.append(Skill(domain=key, level=SkillLevel(lvl), grade=grade))

    st.markdown("<h3>Intérêts & Projet</h3>", unsafe_allow_html=True)
    interests_text = st.text_input(
        "Domaines d'intérêt (séparés par des virgules)",
        placeholder="ex: intelligence artificielle, data science, recherche",
    )
    interests = [i.strip() for i in interests_text.split(",") if i.strip()]

    st.markdown("<h3>Contraintes</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        budget = st.number_input("Budget max (€)", 0, 100000, 5000, 500)
    with c2:
        duration = st.number_input("Durée max (mois)", 1, 60, 24, 1)
    with c3:
        location = st.text_input("Localisation préférée", placeholder="ex: Paris, Lyon")

    c1, c2 = st.columns(2)
    with c1:
        remote_only = st.checkbox("Formation à distance uniquement")
    with c2:
        requires_english = st.checkbox("Accepte les formations en anglais")

    free_text = st.text_area(
        "Décrivez votre projet et votre motivation",
        placeholder="Parlez-nous de vous, de vos ambitions, de ce que vous recherchez...",
        height=100,
    )

    return Student(
        id="custom",
        name=name,
        current_level=level,
        skills=skills,
        interests=interests,
        constraints=Constraint(
            max_budget=float(budget) if budget else None,
            max_duration_months=int(duration) if duration else None,
            preferred_location=location if location else None,
            requires_english=requires_english,
            remote_only=remote_only,
        ),
        free_text=free_text if free_text else None,
    )


# ── Affichage des recommandations ──────────────────────────────────
def display_recommendations(result, engine_name: str):
    if not result.recommendations:
        st.warning("Aucune recommandation trouvée pour ce profil.")
        return

    for i, rec in enumerate(result.recommendations):
        rank_class = "top" if i == 0 else ""
        score_pct = getattr(rec, 'final_score', rec.confidence) * 100
        badge_class = "high" if score_pct >= 60 else "mid" if score_pct >= 35 else "low"

        program = getattr(rec, 'program', None)
        if program is None:
            pid = getattr(rec, 'program_id', None)
            program = next((p for p in PROGRAMS if p.id == pid), None)

        pname = getattr(program, 'name', None) or getattr(rec, 'program_name', '?')
        institution = getattr(program, 'institution', '') if program else ''

        tags_html = ""
        if program:
            tags_html += f'<span class="tag domain">{program.domain.value}</span>'
            tags_html += f'<span class="tag cost">{program.cost} EUR</span>'
            tags_html += f'<span class="tag duration">{program.duration_months} mois</span>'
            tags_html += f'<span class="tag location">{program.location}</span>'

        disagreements = getattr(rec, 'disagreements', None)
        disagreements_html = ""
        if disagreements:
            items = "".join(f"<li>{d}</li>" for d in disagreements)
            disagreements_html = f'<div style="margin-top:10px;padding:10px 14px;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.25);border-radius:6px;font-size:0.85rem;color:var(--warning);"><strong style="color:var(--warning);">Attention :</strong><ul style="margin:4px 0 0 0;padding-left:18px;color:var(--text-muted);">{items}</ul></div>'

        rule_bar = max(0, min(100, getattr(rec, 'rule_score', 0) * 100))
        llm_bar = max(0, min(100, getattr(rec, 'llm_score', rec.confidence) * 100))
        conf_bar = max(0, min(100, rec.confidence * 100))

        html = f"""
        <div class="rec-card {rank_class}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;color:var(--primary-light);">
                        {'#' if i == 0 else '#' + str(i+1)} {pname}
                    </span>
                    <div style="color:var(--text-muted);font-size:0.88rem;margin-top:2px;">
                        {institution}
                    </div>
                </div>
                <span class="score-badge {badge_class}">{score_pct:.0f}/100</span>
            </div>
            <div style="margin-top:10px;">{tags_html}</div>
            <div style="margin-top:14px;display:flex;gap:24px;font-size:0.85rem;">
                <div style="flex:1;">
                    <div style="color:var(--text-muted);margin-bottom:4px;">Moteur Regles</div>
                    <div style="background:var(--border);border-radius:4px;height:8px;">
                        <div style="background:var(--primary);height:8px;border-radius:4px;width:{rule_bar}%;"></div>
                    </div>
                    <div style="color:var(--primary);font-weight:600;margin-top:2px;">{rule_bar:.0f}%</div>
                </div>
                <div style="flex:1;">
                    <div style="color:var(--text-muted);margin-bottom:4px;">Analyse</div>
                    <div style="background:var(--border);border-radius:4px;height:8px;">
                        <div style="background:var(--accent);height:8px;border-radius:4px;width:{llm_bar}%;"></div>
                    </div>
                    <div style="color:var(--accent);font-weight:600;margin-top:2px;">{llm_bar:.0f}%</div>
                </div>
                <div style="flex:1;">
                    <div style="color:var(--text-muted);margin-bottom:4px;">Confiance</div>
                    <div style="background:var(--border);border-radius:4px;height:8px;">
                        <div style="background:var(--success);height:8px;border-radius:4px;width:{conf_bar}%;"></div>
                    </div>
                    <div style="color:var(--success);font-weight:600;margin-top:2px;">{conf_bar:.0f}%</div>
                </div>
            </div>
            <div style="margin-top:14px;padding:12px 16px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;font-size:0.88rem;color:var(--text-muted);line-height:1.6;">
                {rec.justification}
            </div>
            {disagreements_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


# ── Onglet : Saisie du profil ──────────────────────────────────────
def tab_saisie():
    cv_source = st.radio(
        "Source du profil",
        ["Saisie manuelle", "Importer un CV (PDF)"],
        horizontal=True,
    )

    if cv_source == "Importer un CV (PDF)":
        uploaded = st.file_uploader(
            "Déposez votre CV au format PDF",
            type=["pdf"],
            help="Le système extraira automatiquement vos compétences, niveau d'études et intérêts",
        )
        if uploaded:
            with st.spinner("Analyse du CV en cours..."):
                student = parse_cv(pdf_bytes=uploaded.read())

            techs_str = ""
            if student.free_text and "Technologies detectees :" in student.free_text:
                techs_part = student.free_text.split("Technologies detectees :")[1].strip()
                techs_str = f'<p><strong>Technologies :</strong> <span style="color:var(--accent);">{techs_part}</span></p>'

            st.markdown(f"""
            <div class="profile-card" style="border-left:3px solid var(--success);">
                <h4>Profil extrait du CV</h4>
                <p><strong>Nom :</strong> {student.name} &nbsp;|&nbsp;
                   <strong>Niveau :</strong> {student.current_level}</p>
                <p><strong>Domaines :</strong> {', '.join(f'{s.domain} ({s.level.value})' for s in student.skills) if student.skills else 'Aucun détecté'}</p>
                {techs_str}
                <p><strong>Intérêts :</strong> {', '.join(student.interests) if student.interests else 'Aucun détecté'}</p>
            </div>
            """, unsafe_allow_html=True)

            st.info("Vous pouvez ajuster les contraintes ci-dessous avant de lancer l'analyse.")
            c1, c2, c3 = st.columns(3)
            with c1:
                budget = st.number_input("Budget max (€)", 0, 100000, 5000, 500)
            with c2:
                duration = st.number_input("Durée max (mois)", 1, 60, 24, 1)
            with c3:
                location = st.text_input("Localisation préférée", placeholder="ex: Paris, Lyon")
            c1, c2 = st.columns(2)
            with c1:
                remote_only = st.checkbox("Formation à distance uniquement")
            with c2:
                requires_english = st.checkbox("Accepte les formations en anglais")

            student.constraints = Constraint(
                max_budget=float(budget) if budget else None,
                max_duration_months=int(duration) if duration else None,
                preferred_location=location if location else None,
                requires_english=requires_english,
                remote_only=remote_only,
            )
        else:
            st.markdown("""
            <div class="profile-card" style="text-align:center;padding:40px;">
                <p style="color:var(--text-muted);font-size:1.1rem;">
                    Déposez un CV pour extraire automatiquement votre profil
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
    else:
        student = build_student_from_form()

    st.markdown("")
    engine_choice = st.radio(
        "Moteur de recommandation",
        ["Hybride", "Regles uniquement", "LLM uniquement"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if st.button("Obtenir les recommandations", type="primary", use_container_width=True):
        with st.spinner("Analyse du profil en cours..."):
            programs = PROGRAMS
            if engine_choice == "Hybride":
                engine = HybridEngine(alpha=0.5, beta=0.5)
                result = engine.recommend(student, programs)
                display_recommendations(result, "hybride")
            elif engine_choice == "Regles uniquement":
                engine = RuleEngine()
                scored = engine.evaluate(student, programs)
                st.markdown("### Resultats du moteur de regles")
                for sp in scored[:5]:
                    status = "Éligible" if sp.eligible else "Non éligible"
                    color = "var(--success)" if sp.eligible else "var(--danger)"
                    st.markdown(
                        f'<div class="rec-card {"top" if sp.eligible else "warn"}">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                        f'<span style="font-weight:600;color:var(--primary);">{sp.program.name}</span>'
                        f'<span style="color:{color};font-weight:600;font-size:0.85rem;">{status} — {sp.score:.0f}/100</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    if sp.reasons:
                        for r in sp.reasons[:2]:
                            st.caption(f"→ {r}")
            else:
                engine = LLMEngine()
                result = engine.recommend(student, programs)
                display_recommendations(result, "LLM")


# ── Onglet : Profils de test ───────────────────────────────────────
def tab_profils():
    selected = st.selectbox(
        "Choisir un profil predefini",
        SAMPLE_STUDENTS,
        format_func=lambda s: f"{s.name} — {s.id}",
    )
    student = selected

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="profile-card">
            <h4>{student.name}</h4>
            <p><strong>Niveau :</strong> {student.current_level} &nbsp;|&nbsp;
               <strong>Competences :</strong> {', '.join(f'{s.domain} ({s.level.value})' for s in student.skills) if student.skills else '—'} &nbsp;|&nbsp;
               <strong>Interets :</strong> {', '.join(student.interests) if student.interests else '—'}</p>
            <p><strong>Budget :</strong> {student.constraints.max_budget} EUR &nbsp;|&nbsp;
               <strong>Duree max :</strong> {student.constraints.max_duration_months} mois &nbsp;|&nbsp;
               <strong>Localisation :</strong> {student.constraints.preferred_location or '—'}</p>
            {f'<p style="font-style:italic;color:var(--text-muted);">"{student.free_text}"</p>' if student.free_text else ''}
        </div>
        """, unsafe_allow_html=True)

    if st.button("Analyser ce profil", type="primary", key="analyze_sample", use_container_width=True):
        with st.spinner("Analyse en cours..."):
            engine = HybridEngine(alpha=0.5, beta=0.5)
            result = engine.recommend(student, PROGRAMS)
            u = result.uncertainty

            if u.missing_info or u.contradictions or u.warnings:
                warnings_html = ""
                for m in u.missing_info:
                    warnings_html += f'<div style="padding:6px 12px;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.25);border-radius:6px;margin-bottom:6px;font-size:0.85rem;color:var(--warning);">⚠ {m}</div>'
                for c in u.contradictions:
                    warnings_html += f'<div style="padding:6px 12px;background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.25);border-radius:6px;margin-bottom:6px;font-size:0.85rem;color:var(--danger);">✖ {c}</div>'
                for w in u.warnings:
                    warnings_html += f'<div style="padding:6px 12px;background:rgba(126,184,218,0.1);border:1px solid rgba(126,184,218,0.25);border-radius:6px;margin-bottom:6px;font-size:0.85rem;color:var(--primary);">ℹ {w}</div>'
                st.markdown(f'<div class="uncertainty-section"><h4>Analyse du profil</h4>{warnings_html}</div>', unsafe_allow_html=True)

            st.metric("Complétude du profil", f"{u.completeness:.0%}")
            st.markdown("")

            display_recommendations(result, "hybride")


# ── Onglet : Comparaison ───────────────────────────────────────────
def tab_comparaison():
    selected = st.selectbox(
        "Profil a comparer",
        SAMPLE_STUDENTS,
        format_func=lambda s: f"{s.name} — {s.id}",
        key="compare_select",
    )
    student = selected

    if st.button("Lancer la comparaison", type="primary", key="compare_btn", use_container_width=True):
        with st.spinner("Comparaison des moteurs en cours..."):
            rule_engine = RuleEngine()
            llm_engine = LLMEngine()
            hybrid_engine = HybridEngine()

            rule_scored = rule_engine.evaluate(student, PROGRAMS)
            llm_result = llm_engine.recommend(student, PROGRAMS)
            hybrid_result = hybrid_engine.recommend(student, PROGRAMS)

            st.markdown("### Tableau comparatif (Top 5)")
            import pandas as pd
            data = []
            for sp in rule_scored[:5]:
                llm_match = next((r for r in llm_result.recommendations if r.program_id == sp.program.id), None)
                hybrid_match = next((r for r in hybrid_result.recommendations if r.program.id == sp.program.id), None)
                data.append({
                    "Formation": sp.program.name,
                    "Score Regles": sp.score,
                    "Score LLM": round(llm_match.confidence * 100, 1) if llm_match else "-",
                    "Score Hybride": round(hybrid_match.final_score * 100, 1) if hybrid_match else "-",
                    "Eligible": "Oui" if sp.eligible else "Non",
                })
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("### Details par moteur")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Moteur de regles (Top 3)**")
                for sp in rule_scored[:3]:
                    color = "var(--success)" if sp.eligible else "var(--danger)"
                    st.markdown(
                        f'<div style="padding:8px 12px;border-radius:6px;margin-bottom:6px;background:{"rgba(52,211,153,0.12)" if sp.eligible else "rgba(248,113,113,0.12)"};border:1px solid {"rgba(52,211,153,0.25)" if sp.eligible else "rgba(248,113,113,0.25)"};">'
                        f'<span style="font-weight:600;color:var(--text);">{sp.program.name}</span> — '
                        f'<span style="color:{color};font-weight:600;">{sp.score:.0f}</span></div>',
                        unsafe_allow_html=True,
                    )
            with c2:
                st.markdown("**Analyse LLM**")
                for rec in llm_result.recommendations[:3]:
                    st.markdown(
                        f'<div style="padding:8px 12px;border-radius:6px;margin-bottom:6px;background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.25);">'
                        f'<span style="font-weight:600;color:var(--text);">{rec.program_name}</span> — '
                        f'<span style="color:var(--success);font-weight:600;">{rec.confidence:.0%}</span></div>',
                        unsafe_allow_html=True,
                    )


# ── Point d'entrée ─────────────────────────────────────────────────
def main():
    st.markdown("""
    <div class="header-bar">
        <div>
            <h1>Orientation IA</h1>
            <p>Système de recommandation de parcours d'études</p>
        </div>
        <span class="header-badge">Moteur hybride v1.0</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Saisie du profil", "Profils de test", "Comparaison"])

    with tab1:
        tab_saisie()
    with tab2:
        tab_profils()
    with tab3:
        tab_comparaison()

    st.markdown("---")
    st.caption("Système de raisonnement hybride — Moteur symbolique + Analyse contextuelle — Gestion explicite de l'incertitude")


if __name__ == "__main__":
    main()
