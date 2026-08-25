# Membre 5 — Tests, Qualité et Documentation

**Fichiers responsables :** `tests/`, `README.md`, `requirements.txt`

## Rôle

Écrire les tests unitaires et d'intégration, mesurer la qualité du système, et documenter le projet.

## Fichiers gérés

| Fichier | Description |
|---------|-------------|
| `tests/test_rule_engine.py` | 20 tests du moteur de règles |
| `tests/test_uncertainty.py` | 12 tests de l'analyse d'incertitude |
| `tests/test_hybrid.py` | 12 tests de l'intégration hybride |
| `tests/test_comparison.py` | 5 tests de comparaison des moteurs |
| `tests/test_cv_parser.py` | 9 tests du parser de CV |
| `README.md` | Documentation complète du projet |
| `requirements.txt` | Dépendances Python |

---

## Bilan des tests : 50/50 OK

```
tests/test_rule_engine.py     — 20 tests  ✅
tests/test_uncertainty.py     — 12 tests  ✅
tests/test_hybrid.py          — 12 tests  ✅
tests/test_comparison.py      —  5 tests  ✅
tests/test_cv_parser.py       —  9 tests  ✅
───────────────────────────────────────────
Total                         — 50 tests  ✅  (< 1 seconde)
```

---

## Détail par fichier de test

### `test_rule_engine.py` — 20 tests

| # | Test | Vérification |
|---|------|-------------|
| 1 | `test_budget_filter` | Rejet si coût > budget |
| 2 | `test_duration_filter` | Rejet si durée > max |
| 3 | `test_prereq_filter` | Rejet si prérequis manquant |
| 4 | `test_level_filter` | Rejet si niveau insuffisant |
| 5 | `test_skill_relevance` | Score si compétences matchent |
| 6 | `test_domain_alignment` | Pénalité -15% si hors domaine |
| 7 | `test_interest_match` | Bonus si domaine = intérêts |
| 8 | `test_location_match` | Bonus si localisation correcte |
| 9 | `test_remote_match` | Bonus si formation à distance |
| 10 | `test_empty_student` | Gestion profil vide |
| 11 | `test_all_rejected` | Retourne liste vide si tout rejeté |
| 12 | `test_multiple_skills` | Compétences multiples |
| 13 | `test_score_range` | Score toujours entre 0 et 100 |
| 14 | `test_recommendations_count` | Retourne ≤ 5 recommandations |
| 15 | `test_execution_time` | < 100ms pour 12 formations |
| 16-20 | Cas spécifiques | Edge cases, intégration |

### `test_uncertainty.py` — 12 tests

| # | Test | Vérification |
|---|------|-------------|
| 1 | `test_complete_profile` | Complétude = 100% |
| 2 | `test_empty_profile` | Complétude = 0%, alertes |
| 3 | `test_missing_skills` | Détecte compétences manquantes |
| 4 | `test_missing_interests` | Détecte intérêts manquants |
| 5 | `test_level_contradiction` | Niveau élevé ≠ compétences |
| 6 | `test_domain_contradiction` | Domaine ≠ intérêts |
| 7 | `test_zero_budget` | Alerte budget = 0€ |
| 8 | `test_atypical_profile` | Alerte profil atypique |
| 9 | `test_clarification_questions` | Génère des questions |
| 10 | `test_completeness_score` | Score proportionnel |
| 11 | `test_warnings` | Alertes pour profils extrêmes |
| 12 | `test_integration` | Combinaison multiple |

### `test_hybrid.py` — 12 tests

| # | Test | Vérification |
|---|------|-------------|
| 1 | `test_alpha_beta_fusion` | Formule de fusion correcte |
| 2 | `test_equal_weights` | α=β=0.5 donne score moyen |
| 3 | `test_rules_only` | α=1, β=0 → score règles |
| 4 | `test_llm_only` | α=0, β=1 → score LLM |
| 5 | `test_disagreement_detection` | Détecte écart > 20% |
| 6 | `test_no_disagreement` | Pas d'alerte si accord |
| 7 | `test_confidence_reduction` | Confiance réduite si incertitude |
| 8 | `test_confidence_amplification` | Confiance amplifiée si accord |
| 9 | `test_recommendations_sorted` | Tri par score décroissant |
| 10 | `test_max_recommendations` | ≤ 5 résultats |
| 11 | `test_execution_time` | < 10 secondes |
| 12 | `test_integration_10_profiles` | 10 profils de test |

### `test_comparison.py` — 5 tests

| # | Test | Vérification |
|---|------|-------------|
| 1 | `test_accuracy` | Formations attendues dans top 3 |
| 2 | `test_performance_rules` | Règles < 100ms |
| 3 | `test_performance_hybrid` | Hybride < 10s |
| 4 | `test_coherence` | Accord ≥ 1/3 entre moteurs |
| 5 | `test_robustness` | Résistance aux contradictions |

### `test_cv_parser.py` — 9 tests

| # | Test | Vérification |
|---|------|-------------|
| 1 | `test_name_detection` | Nom extrait correctement |
| 2 | `test_level_detection` | Niveau = PLUS HAUT mentionné |
| 3 | `test_skills_detection` | 25+ technologies reconnues |
| 4 | `test_interests_technical` | Intérêts techniques extraits |
| 5 | `test_interests_from_section` | Intérêts depuis section dédiée |
| 6 | `test_empty_pdf` | Fallback gracieux |
| 7 | `test_multi_column` | Extraction multi-colonnes |
| 8 | `test_tech_mapping` | Technologies → intérêts techniques |
| 9 | `test_integration` | Profil complet extrait |

---

## Exécution des tests

```bash
# Tous les tests
python -m pytest tests/ -v

# Un fichier spécifique
python -m pytest tests/test_rule_engine.py -v

# Avec couverture
python -m pytest tests/ --cov=src --cov-report=term-missing

# Rapport HTML
python -m pytest tests/ --html=rapport_tests.html
```

---

## Métriques de qualité

| Métrique | Valeur | Objectif |
|----------|--------|----------|
| Tests passants | 50/50 | ≥ 50 ✅ |
| Temps d'exécution | < 1s | < 10s ✅ |
| Cas limites | 3+ | ≥ 3 ✅ |
| Profils de test | 10 | ≥ 10 ✅ |
| Formations testées | 12 | ≥ 10 ✅ |

---

## Documentation

| Document | Contenu |
|----------|---------|
| `README.md` | Architecture, installation, utilisation, rôles |
| `docs/membre1_*.md` | Formalisation des données |
| `docs/membre2_*.md` | Moteur de règles |
| `docs/membre3_*.md` | LLM et incertitude |
| `docs/membre4_*.md` | Intégration et interface |
| `docs/membre5_*.md` | Tests et qualité |
