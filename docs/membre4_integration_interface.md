# Membre 4 — Intégration Hybride et Interface Streamlit

**Fichiers responsables :** `src/engines/hybrid.py`, `app.py`, `src/utils/cv_parser.py`

## Rôle

Fusionner les résultats des deux moteurs (règles + LLM) en un score unique, détecter les désaccords, et fournir l'interface utilisateur via Streamlit.

## Fichiers gérés

| Fichier | Description |
|---------|-------------|
| `src/engines/hybrid.py` | Intégrateur hybride avec fusion pondérée |
| `app.py` | Application Streamlit (3 onglets, thème sombre) |
| `src/utils/cv_parser.py` | Extraction automatique de CV PDF |

---

## Partie 1 : Intégration Hybride (`hybrid.py`)

### Formule de fusion

```
score_hybride = α × score_règles + β × score_llm
```

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `alpha` | 0.5 | Poids du moteur de règles |
| `beta` | 0.5 | Poids du moteur LLM |

### Détection de désaccords

```python
if abs(regle_rank - llm_rank) > 2:
    # Désaccord détecté
    # Affiche une alerte dans l'interface
```

Types de désaccords :
- **Écart de classement** : les deux moteurs n'ont pas la même formation en #1
- **Écart de score** : un moteur donne un score élevé, l'autre faible
- **Conflit domain** : un moteur recommande hors domaine

### Utilisation

```python
from src.engines.hybrid import HybridEngine

engine = HybridEngine(alpha=0.5, beta=0.5)
result = engine.recommend(student, programs)

for rec in result.recommendations:
    print(f"{rec.program.name}")
    print(f"  Score: {rec.final_score:.0f}/100")
    print(f"  Règles: {rec.rule_score:.0f}% | LLM: {rec.llm_score:.0f}%")
    print(f"  Confiance: {rec.confidence:.0f}%")
    if rec.disagreement:
        print(f"  ⚠ Désaccord: {rec.disagreement}")
```

---

## Partie 2 : Interface Streamlit (`app.py`)

### Thème et design

| Élément | Valeur |
|---------|--------|
| Couleur de fond | `#0f1923` (bleu foncé) |
| Police | Inter, monospace pour code |
| Palette | Bleu `#1a56db`, Ambre `#d97706` |
| Style | Cards, barres de progression, badges |

### Onglets de l'application

#### Onglet 1 : Saisie du profil

- **Formulaire** : nom, niveau, compétences (domaine + niveau), intérêts
- **Contraintes** : budget, durée, localisation, langue, remote
- **Import CV** : toggle pour activer l'import PDF
- **Profils prédéfinis** : 10 profils de test en un clic

#### Onglet 2 : Recommandations

- **Bouton** : "Lancer la recommandation"
- **Affichage** : top 3-5 formations avec :
  - Score final (barre de progression)
  - Score règles vs LLM (barre split)
  - Justification détaillée
  - Points forts / points faibles
  - Alertes de désaccord
  - Score de confiance

#### Onglet 3 : Analyse détaillée

- **Incertitude** : rapport de complétude
- **Désaccords** : détails des conflits entre moteurs
- **Comparaison** : tableau des 10 formations classées

### Import CV (`cv_parser.py`)

```
PDF uploadé
    │
    ▼
┌───────────────────┐
│ Extraction texte   │  pdfplumber (gère multi-colonnes)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Détection profil  │
│  ● Nom            │  Première ligne en majuscules
│  ● Niveau         │  Le PLUS HAUT niveau mentionné
│  ● Compétences    │  25+ technologies reconnues
│  ● Intérêts       │  Techniques + centres d'intérêt
│  ● Contraintes    │  Budget, durée si mentionnés
└────────┬──────────┘
         │
         ▼
Profil pré-rempli → Vérification → Lancement
```

### FonctionnalitésCV

- **25+ technologies** détectées : React, Angular, Django, Spring Boot, Docker, Python, etc.
- **Intérêts techniques** extraits du profil et des technologies (pas seulement "nager", "lecture")
- **Niveau d'études** : prend le PLUS HAUT niveau mentionné (M1 = bac+4)
- **Fallback gracieux** : si le CV est vide ou illisible, retourne un profil par défaut

### Lancement

```bash
streamlit run app.py
```

---

## Tests associés

### `tests/test_hybrid.py` — 12 tests

| Catégorie | Tests |
|-----------|-------|
| Fusion | Pondération α/β, scores identiques, complémentaires |
| Désaccords | Détection écart, alertes affichées |
| Confiance | Réduction si incertitude, amplification si accord |
| Performance | < 10 secondes pour 12 formations |

### `tests/test_cv_parser.py` — 9 tests

| Catégorie | Tests |
|-----------|-------|
| Extraction | Nom, niveau, compétences, intérêts |
| Technologies | Détection multi-colonnes, 25+ techs |
| Niveaux | bac+3, M1, M2, doctorat |
| Fallback | CV vide, illisible, multi-colonnes |
| Intérêts | Techniques extraits du profil |
