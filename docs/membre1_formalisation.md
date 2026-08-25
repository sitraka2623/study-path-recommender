# Membre 1 — Formalisation et Base de Connaissances

**Fichiers responsables :** `src/models/student.py`, `src/models/program.py`, `data/`

## Rôle

Modéliser les données du système : profils étudiants, formations, compétences et contraintes. Charger le catalogue de formations et les profils de test depuis des fichiers JSON.

## Fichiers gérés

| Fichier | Description |
|---------|-------------|
| `src/models/student.py` | Modèle `Student` avec compétences, niveaux, intérêts et contraintes |
| `src/models/program.py` | Modèle `Program` avec domaine, prérequis, coût, durée |
| `data/programs_catalog.json` | 12 formations (licence → doctorat, 4 domaines) |
| `data/sample_students.json` | 10 profils de test dont 3 cas limites |

## Structure des données

### Étudiant (`student.py`)

```python
class SkillLevel(Enum):
    NONE, BEGINNER, INTERMEDIATE, ADVANCED, EXPERT

class Skill:
    domain: str          # "informatique", "mathematiques", etc.
    level: SkillLevel
    grade: str | None    # "15/20", "A", etc.

class Constraint:
    max_budget: float | None
    max_duration_months: int | None
    preferred_location: str | None
    preferred_language: str | None
    prefers_remote: bool

class Student:
    id: str
    name: str
    current_level: str   # "bac+3", "M1", "doctorat"
    skills: list[Skill]
    interests: list[str]
    constraints: Constraint
    free_text: str
```

### Formation (`program.py`)

```python
class Domain(Enum):
    INFORMATIQUE, DESIGN, DATA_SCIENCE, INTELLIGENCE_ARTIFICIELLE

class Prereq:
    domain: str
    required: bool
    min_level: str       # "beginner", "intermediate", etc.

class Program:
    id: str
    name: str
    institution: str
    domain: Domain
    duration_months: int
    cost: float
    skills_taught: list[str]
    prerequisites: list[Prereq]
    location: str
    is_remote: bool
```

## Catalogue de formations (12)

| ID | Formation | Domaine | Durée | Coût |
|----|-----------|---------|-------|------|
| L1 | Licence Informatique | informatique | 36 mois | 170€ |
| L2 | Licence Design Digital | design | 36 mois | 200€ |
| L3 | Licence Droit | droit | 36 mois | 170€ |
| M1 | Master IA | intelligence_artificielle | 24 mois | 250€ |
| M2 | Master Data Science | data_science | 24 mois | 300€ |
| M3 | Master Génie Logiciel | informatique | 24 mois | 243€ |
| C1 | Certificat UX/UI | design | 3 mois | 39€ |
| C2 | Certificat Data Analytics | data_science | 4 mois | 45€ |
| C3 | Certificat IA | intelligence_artificielle | 6 mois | 99€ |
| D1 | Dev Web Full Stack | informatique | 6 mois | 499€ |
| D2 | Bootcamp Data | data_science | 3 mois | 599€ |
| D3 | Formation Cybersécurité | informatique | 9 mois | 399€ |

## Profils de test (10, dont 3 cas limites)

| ID | Type | Description |
|----|------|-------------|
| S01 | Normal | Sci info, bonnes notes, veut IA |
| S02 | Normal | Bio → switch data science |
| S03 | Normal | Bac général, créative, marketing |
| **S04** | **Limite** | **Profil totalement vide** |
| **S05** | **Limite** | **Double compétence info+arts** |
| **S06** | **Limite** | **Budget = 0€** |
| S07 | Normal | Étrangère, maths → data finance |
| S08 | Normal | Sans diplôme, veut coder, remote |
| S09 | Normal | Psycho → cognitive science / IA |
| S10 | Normal | Notes médiocres mais ambitieux |

## Tests associés

Les modèles sont testés indirectement via les 50 tests du projet (rule_engine, hybrid, uncertainty, cv_parser, comparison).
