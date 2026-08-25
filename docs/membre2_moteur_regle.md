# Membre 2 — Moteur de Règles Symbolique

**Fichiers responsables :** `src/engines/rule_engine.py`, `config/rules.json`

## Rôle

Implémenter le moteur de raisonnement symbolique qui applique des règles formelles pour filtrer et classer les formations candidates.

## Fichiers gérés

| Fichier | Description |
|---------|-------------|
| `src/engines/rule_engine.py` | Moteur de règles avec filtrage dur + scoring mou |
| `config/rules.json` | 10 règles formelles (R01-R10) en DSL |

## Architecture du moteur

```
Profil étudiant + Catalogue formations
            │
            ▼
    ┌───────────────────┐
    │  FILTRAGE DUR     │  Élimine les formations non conformes
    │  (Hard Filtering) │  Budget, durée, prérequis obligatoires
    └────────┬──────────┘
             │
             ▼
    ┌───────────────────┐
    │  SCORING MOU      │  Classe les formations restantes
    │  (Soft Scoring)   │  5 critères pondérés
    └────────┬──────────┘
             │
             ▼
    Formations classées par score (0-100)
```

## Règles formelles (R01-R10)

### Filtrage dur (rejette la formation)

| Règle | Condition | Action |
|-------|-----------|--------|
| R01 | Niveau étudiant < niveau minimum requis | Rejet |
| R02 | Niveau étudiant > niveau maximum requis | Rejet |
| R03 | Coût annuel > budget max étudiant | Rejet |
| R04 | Durée > durée max souhaitée | Rejet |
| R07 | Prérequis obligatoire non satisfait | Rejet |

### Scoring mou (ajoute/retire des points)

| Règle | Critère | Poids |
|-------|---------|-------|
| R05 | Localisation correspondante | 12% |
| R06 | Formation à distance (si demandé) | 8% |
| R08 | Niveau de compétence suffisant | 10% |
| R09 | Formation en langue demandée | 5% |
| R10 | Domaine cohérent avec intérêts | 20% |

### Score total (5 critères)

| Critère | Poids | Description |
|---------|-------|-------------|
| Pertinence des compétences | 35% | Compétences étudiant ↔ compétences enseignées |
| Cohérence des prérequis | 25% | Prérequis satisfaits + niveau suffisant |
| Pertinence du domaine | 20% | Domaine formation ↔ intérêts étudiant |
| Localisation | 12% | Ville, remote, langue |
| Durée | 8% | Conformité durée souhaitée |

## Facteur d'alignement de domaine

Pénalité de **0.15** appliquée quand le domaine de la formation n'a aucun lien avec les compétences ou intérêts de l'étudiant. Empêche les formations hors sujet (ex: "Licence de Droit" pour un développeur).

```python
# Exemple de pénalité
if programme.domaine not in domains_etudiant:
    score *= (1 - 0.15)  # -15%
```

## Utilisation

```python
from src.engines.rule_engine import RuleEngine

engine = RuleEngine()
result = engine.recommend(student, programs)

# Résultat
for rec in result.recommendations:
    print(f"{rec.program.name}: {rec.score}/100")
    print(f"  Règles: {rec.rules_applied}")
```

## Tests associés

Fichier : `tests/test_rule_engine.py` — 20 tests

| Catégorie | Tests |
|-----------|-------|
| Filtrage dur | Rejet budget, durée, prérequis, niveau |
| Scoring | Compétences, domaines, localisation, durées |
| Cas limites | Étudiant vide, sans compétences, tous rejetés |
| Intégration | 10 profils de test, temps d'exécution |
| Performance | < 100ms pour 12 formations |
