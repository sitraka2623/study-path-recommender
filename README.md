# 🎓 Système de Recommandation de Parcours d'Études

Système de raisonnement hybride combinant un **moteur symbolique à base de règles** et un **LLM guidé par des contraintes formelles** pour recommander des formations adaptées au profil d'un étudiant.

## 🎯 Problème

**Entrées :** Profil étudiant (compétences, intérêts, contraintes, description libre)  
**Sorties :** 2-3 formations recommandées avec score, justification et niveau de confiance  
**Gestion de l'incertitude :** Profils incomplets, contradictions, informations manquantes

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│     Interface Streamlit (app.py) │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    Moteur Hybride (hybrid.py)    │
│    Fusion Rules + LLM + Incert.  │
└──────┬───────────────┬──────────┘
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│ Moteur Rules │ │  LLM + RAG   │
│ (rule_engine)│ │ (llm_engine) │
└──────────────┘ └──────────────┘
       ▼               ▼
┌─────────────────────────────────┐
│  Base de connaissances (JSON)    │
│  Catalogue formations + règles   │
└─────────────────────────────────┘
```

## 🚀 Installation et lancement

```bash
# 1. Cloner le projet
cd study-path-recommender

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Installer Ollama (gratuit, local)
# Téléchargez depuis https://ollama.com puis :
ollama pull llama3.2

# 4. Lancer les tests
python -m pytest tests/ -v

# 5. Lancer l'application
streamlit run app.py
```

## 📁 Structure du projet

```
study-path-recommender/
├── app.py                         # Interface Streamlit
├── requirements.txt               # Dépendances Python
├── config/
│   ├── .env.example               # Template de configuration
│   └── rules.json                 # Règles formelles du moteur symbolique
├── data/
│   ├── programs_catalog.json      # 12 formations (licence → doctorat)
│   └── sample_students.json       # 10 profils de test (dont 3 cas limites)
├── src/
│   ├── models/
│   │   ├── student.py             # Modèle étudiant + compétences
│   │   └── program.py             # Modèle formation + prérequis
│   ├── engines/
│   │   ├── rule_engine.py         # Approche 1: Moteur de règles symbolique
│   │   ├── llm_engine.py          # Approche 2: LLM guidé par règles (RAG)
│   │   └── hybrid.py              # Intégrateur hybride des deux approches
│   ├── knowledge/
│   │   └── loader.py              # Chargement des données JSON
│   └── utils/
│       └── uncertainty.py         # Analyse d'incertitude et de complétude
└── tests/
    ├── test_rule_engine.py        # Tests unitaires moteur de règles
    ├── test_uncertainty.py        # Tests analyse d'incertitude
    ├── test_hybrid.py             # Tests intégration hybride
    └── test_comparison.py         # Comparaison 10 cas de test
```

## 🔧 Approches implémentées

### Approche 1 : Moteur Symbolique (Règles)
- **Filtrage** par contraintes dures (prérequis, budget, durée)
- **Scoring** par préférences (intérêts, localisation, satisfaction)
- 10 règles formelles (R01-R10) avec poids configurables
- Déterministe, explicable, vérifiable

### Approche 2 : LLM Guidé par Règles (RAG)
- Pré-filtrage des formations avant envoi au LLM
- Prompt structuré avec sortie JSON contrainte
- **Fallback déterministe** quand le LLM n'est pas disponible
- Analyse du langage naturel et justification contextuelle

### Intégration Hybride
- Score final = α × règles + β × LLM (α, β configurables)
- Détection automatique des **désaccords** entre moteurs
- Modificateur de confiance basé sur l'analyse d'incertitude

## 📊 Cas de test (10 cas, 3 limites)

| ID | Type | Description |
|----|------|-------------|
| S01 | Normal | Sci info, bonnes notes, veut IA |
| S02 | Normal | Bio → switch data science |
| S03 | Normal | Bac général, créative, marketing |
| S04 | **Limite** | Profil totalement vide |
| S05 | **Limite** | Profil atypique double competence info+arts |
| S06 | **Limite** | Budget = 0€ |
| S07 | Normal | Étrangère, maths → data finance |
| S08 | Normal | Sans diplôme, veut coder, remote |
| S09 | Normal | Psycho → cognitive science / IA |
| S10 | Normal | Notes médiocres mais ambitieux |

## 📈 Évaluation

Le fichier `tests/test_comparison.py` mesure :
- **Exactitude** : les formations attendues sont dans l'éligible
- **Temps** : < 100ms pour les règles, < 10s pour l'hybride
- **Cohérence** : accord entre les deux moteurs (overlap ≥ 1/3)
- **Complétude** : détection des profils vides et contradictions

## 👥 Organisation (5 rôles)

| Rôle | Fichiers | Responsabilités |
|------|----------|-----------------|
| Formalisation/Knowledge | `student.py`, `program.py`, `data/` | Modélisation des données, catalogue |
| Moteur Symbolique | `rule_engine.py`, `rules.json` | Règles formelles, scoring |
| Incertitude/LLM | `llm_engine.py`, `uncertainty.py` | LLM, RAG, gestion incertitude |
| Intégration/Interface | `hybrid.py`, `app.py` | Fusion, Streamlit |
| Tests/Qualité | `tests/`, `README.md` | Tests, évaluation comparative |

## 📝 Notes

- Le système fonctionne **sans clé API** grâce au fallback déterministe
- Les poids α/β de la fusion sont configurables dans `HybridEngine`
- Ajoutez des formations dans `data/programs_catalog.json` pour enrichir la base
