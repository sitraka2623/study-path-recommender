from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from src.models.student import Student


@dataclass
class UncertaintyReport:
    completeness: float = 0.0
    contradictions: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_modifier: float = 0.0


class UncertaintyAnalyzer:
    """
    Analyse l'incertitude d'un profil étudiant.
    Détecte les informations manquantes, les contradictions et les profils incomplets.
    """

    CRITICAL_FIELDS_WEIGHTS = {
        "current_level": 0.20,
        "skills": 0.25,
        "interests": 0.20,
        "budget": 0.10,
        "duration": 0.10,
        "location": 0.05,
        "free_text": 0.10,
    }

    def analyze(self, student: Student) -> UncertaintyReport:
        report = UncertaintyReport()
        report.completeness = self._compute_completeness(student)
        report.missing_info = self._detect_missing(student)
        report.contradictions = self._detect_contradictions(student)
        report.warnings = self._detect_warnings(student)
        report.confidence_modifier = self._compute_modifier(report)
        return report

    def _compute_completeness(self, student: Student) -> float:
        score = 0.0
        if student.current_level:
            score += self.CRITICAL_FIELDS_WEIGHTS["current_level"]
        if student.skills:
            score += self.CRITICAL_FIELDS_WEIGHTS["skills"] * min(1.0, len(student.skills) / 3)
        if student.interests:
            score += self.CRITICAL_FIELDS_WEIGHTS["interests"] * min(1.0, len(student.interests) / 2)
        if student.constraints.max_budget is not None:
            score += self.CRITICAL_FIELDS_WEIGHTS["budget"]
        if student.constraints.max_duration_months is not None:
            score += self.CRITICAL_FIELDS_WEIGHTS["duration"]
        if student.constraints.preferred_location:
            score += self.CRITICAL_FIELDS_WEIGHTS["location"]
        if student.free_text:
            score += self.CRITICAL_FIELDS_WEIGHTS["free_text"]
        return round(min(1.0, score), 2)

    def _detect_missing(self, student: Student) -> list[str]:
        missing = []
        if not student.current_level:
            missing.append("Niveau d'études actuel non renseigné")
        if not student.skills:
            missing.append("Aucune compétence renseignée")
        elif len(student.skills) < 2:
            missing.append("Peu de compétences renseignées (< 2)")
        if not student.interests:
            missing.append("Aucun intérêt renseigné")
        if student.constraints.max_budget is None:
            missing.append("Budget non renseigné")
        if student.constraints.max_duration_months is None:
            missing.append("Durée maximale non renseignée")
        if not student.constraints.preferred_location:
            missing.append("Localisation préférée non renseignée")
        if not student.free_text:
            missing.append("Pas de description libre du projet")
        return missing

    def _detect_contradictions(self, student: Student) -> list[str]:
        contradictions = []

        high_skills = [s for s in student.skills if s.level.value in ("advanced", "expert")]
        low_grades = [s for s in student.skills if s.grade is not None and s.grade < 10]
        if high_skills and low_grades:
            high_domains = [s.domain for s in high_skills]
            low_domains = [s.domain for s in low_grades]
            overlap = set(high_domains) & set(low_domains)
            if overlap:
                contradictions.append(
                    f"Compétences élevées mais notes basses dans: {', '.join(overlap)}"
                )

        if student.current_level in ("bac+4", "bac+5", "master", "doctorat"):
            basic_skills = [s for s in student.skills if s.level.value == "none"]
            if len(basic_skills) > len(student.skills) / 2 and student.skills:
                contradictions.append(
                    "Niveau d'études avancé mais très peu de compétences de base"
                )

        if student.free_text:
            text_lower = student.free_text.lower()
            if "pas感兴趣" in text_lower or "aucun" in text_lower or "pas d'intérêt" in text_lower:
                if student.interests:
                    contradictions.append("Intérêts renseignés mais texte suggère un désintérêt")

        return contradictions

    def _detect_warnings(self, student: Student) -> list[str]:
        warnings = []
        if student.constraints.max_budget is not None and student.constraints.max_budget == 0:
            warnings.append("Budget à 0€ - seules les formations gratuites sont éligibles")
        if student.constraints.max_duration_months is not None and student.constraints.max_duration_months < 3:
            warnings.append("Durée très courte (< 3 mois) - options limitées")
        grades = [s.grade for s in student.skills if s.grade is not None]
        if grades and sum(grades) / len(grades) < 10:
            warnings.append("Moyenne générale inférieure à 10/20")
        return warnings

    def _compute_modifier(self, report: UncertaintyReport) -> float:
        modifier = 0.0
        modifier -= len(report.missing_info) * 0.03
        modifier -= len(report.contradictions) * 0.08
        modifier -= len(report.warnings) * 0.02
        modifier += report.completeness * 0.1
        return round(max(-0.5, min(0.2, modifier)), 3)
