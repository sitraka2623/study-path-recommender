# Membre 3 — Moteur LLM et Analyse d'Incertitude

**Fichiers responsables :** `src/engines/llm_engine.py`, `src/utils/uncertainty.py`

## Rôle

Implémenter le moteur de raisonnement basé sur un LLM (OpenAI/Ollama/fallback) et le module d'analyse d'incertitude pour gérer les profils incomplets ou contradictoires.

## Fichiers gérés

| Fichier | Description |
|---------|-------------|
| `src/engines/llm_engine.py` | Moteur LLM avec 3 fournisseurs + fallback |
| `src/utils/uncertainty.py` | Analyse de complétude et de contradictions |

---

## Partie 1 : Moteur LLM (`llm_engine.py`)

### Architecture

```
Profil étudiant + Catalogue formations
            │
            ▼
    ┌───────────────────┐
    │  Pré-filtrage     │  Réduit le catalogue (budget×1.5, durée×2)
    └────────┬──────────┘
             │
             ▼
    ┌───────────────────┐
    │  Choix fournisseur│
    │  ● OpenAI (API)   │  GPT-4o-mini
    │  ● Ollama (local) │  llama3.2
    │  ● Fallback       │  Déterministe
    └────────┬──────────┘
             │
             ▼
    Résultat : formations + confiance + justification
```

### Trois fournisseurs

| Fournisseur | Modèle | Config `.env` | Avantage |
|-------------|--------|----------------|----------|
| OpenAI | GPT-4o-mini | `LLM_PROVIDER=openai` | Qualité, rapidité |
| Ollama | llama3.2 | `LLM_PROVIDER=ollama` | Gratuit, local, privé |
| Fallback | — | `LLM_PROVIDER=fallback` | Pas besoin d'API |

### Prompt envoyé au LLM

```
Tu es un conseiller orientation expert.
RÈGLES:
1. Te baser UNIQUEMENT sur le catalogue fourni
2. Justifier chaque recommandation
3. Signaler les prérequis manquants
4. Score de confiance (0-1) pour chaque formation
5. Identifier les risques du profil

FORMAT: JSON strict avec recommendations[]
```

### Mode fallback (sans LLM)

Quand aucun LLM n'est disponible, le système effectue un raisonnement déterministe :

1. **Vérifie la correspondance domaine** — pénalité de -0.3 si hors domaine
2. **Évalue les prérequis** — +0.05 si satisfaits, -0.1 sinon
3. **Vérifie le budget** — +0.05 si dans le budget
4. **Vérifie la localisation** — +0.05 si correspond
5. **Trie** par confiance décroissante

### Utilisation

```python
from src.engines.llm_engine import LLMEngine

engine = LLMEngine()  # Lit config/.env automatiquement
result = engine.recommend(student, programs)

print(f"Provider utilisé: {result.used_fallback and 'fallback' or 'llm'}")
print(f"Latence: {result.latency_ms:.0f}ms")
for rec in result.recommendations:
    print(f"  {rec.program_name}: {rec.confidence:.0%}")
    print(f"    {rec.justification}")
```

---

## Partie 2 : Analyse d'Incertitude (`uncertainty.py`)

### Types d'incertitude détectés

| Type | Description | Exemple |
|------|-------------|---------|
| **Informations manquantes** | Champs vides du profil | Pas de compétences renseignées |
| **Contradictions** | Données incohérentes | Niveau bac+4 sans compétences |
| **Alertes** | Profil atypique | Budget = 0€, 0 intérêts |

### Structure de rapport

```python
@dataclass
class UncertaintyReport:
    completeness_score: float    # 0.0 (vide) → 1.0 (complet)
    missing_info: list[str]      # ["compétences", "intérêts"]
    contradictions: list[str]    # ["niveau élevé mais compétences faibles"]
    warnings: list[str]          # ["Profil très complet"]
    needs_clarification: list[str]  # Questions à poser
```

### Utilisation

```python
from src.utils.uncertainty import UncertaintyAnalyzer

analyzer = UncertaintyAnalyzer()
report = analyzer.analyze(student)

print(f"Complétude: {report.completeness_score:.0%}")
for m in report.missing_info:
    print(f"  Manquant: {m}")
for c in report.contradictions:
    print(f"  Contradiction: {c}")
```

### Impact sur la recommandation

Le rapport d'incertitude est utilisé par le moteur hybride pour :
- Réduire la confiance si le profil est incomplet
- Afficher des alertes dans l'interface Streamlit
- Proposer des questions de clarification

---

## Tests associés

### `tests/test_uncertainty.py` — 12 tests

| Catégorie | Tests |
|-----------|-------|
| Complétude | Profil complet, vide, partiel |
| Contradictions | Niveau ≠ compétences, domaine ≠ intérêts |
| Alertes | Budget zéro, profil atypique |
| Questions | Génération de questions de clarification |

### `tests/test_comparison.py` — 5 tests

| Test | Vérification |
|------|-------------|
| Exactitude | Formations attendues dans le top 3 |
| Temps | Règles < 100ms, hybride < 10s |
| Cohérence | Accord ≥ 1/3 entre moteurs |
| Complétude | Détection des profils vides |
| Robustesse | Résistance aux contradictions |
