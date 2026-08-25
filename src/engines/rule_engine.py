from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.models.student import Student, SkillLevel
from src.models.program import Program


LEVEL_ORDER = ["none", "beginner", "intermediate", "advanced", "expert"]

STUDENT_LEVEL_RANKING = {
    "sans_diplome": 0, "bac": 1, "bac+1": 2, "bac+2": 3,
    "bac+3": 4, "licence": 4, "bac+4": 5, "bac+5": 6,
    "master": 6, "doctorat": 7,
}

PROGRAM_LEVEL_RANKING = {
    "licence": 0, "diplome_pro": 0, "bootcamp": 0, "certificat": 0,
    "master": 1, "mba": 1, "diplome_ingenieur": 1, "doctorat": 2,
}


@dataclass
class RuleViolation:
    rule_id: str
    rule_name: str
    message: str
    severity: str  # "hard" | "soft"


@dataclass
class ScoredProgram:
    program: Program
    score: float
    eligible: bool
    rule_score: float = 0.0
    preference_score: float = 0.0
    violations: list[RuleViolation] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class RuleEngine:
    """
    Moteur symbolique de recommandation basé sur des règles formelles.
    Deux phases : filtrage (contraintes dures) puis scoring (préférences).
    """

    def __init__(self, weights: dict | None = None):
        self.weights = weights or {
            "prereq_match": 0.30,
            "interest_match": 0.25,
            "skill_relevance": 0.15,
            "budget_fit": 0.10,
            "duration_fit": 0.10,
            "location_match": 0.05,
            "satisfaction": 0.05,
        }

    def evaluate(self, student: Student, programs: list[Program]) -> list[ScoredProgram]:
        results = []
        for program in programs:
            scored = self._evaluate_single(student, program)
            results.append(scored)
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _evaluate_single(self, student: Student, program: Program) -> ScoredProgram:
        violations: list[RuleViolation] = []
        reasons: list[str] = []
        eligible = True

        # === PHASE 1 : CONTRAINTES DURES (filtres) ===

        # R01 : Prérequis obligatoires
        prereq_ok, prereq_msg = self._check_prerequisites(student, program)
        if not prereq_ok:
            violations.append(RuleViolation("R01", "Prérequis obligatoires", prereq_msg, "hard"))
            eligible = False
        else:
            reasons.append(prereq_msg)

        # R02 : Budget
        if student.constraints.max_budget is not None:
            if program.cost > student.constraints.max_budget:
                violations.append(RuleViolation(
                    "R02", "Budget dépassé",
                    f"Coût {program.cost}€ > budget {student.constraints.max_budget}€", "hard"
                ))
                eligible = False

        # R03 : Durée
        if student.constraints.max_duration_months is not None:
            if program.duration_months > student.constraints.max_duration_months:
                violations.append(RuleViolation(
                    "R03", "Durée dépassée",
                    f"Durée {program.duration_months} mois > max {student.constraints.max_duration_months} mois", "hard"
                ))
                eligible = False

        # === PHASE 2 : SCORING DES PRÉFÉRENCES ===
        rule_score = 0.0

        # R04 : Correspondance domaine-intérêts
        interest_score = self._score_interest_match(student, program)
        rule_score += interest_score * self.weights["interest_match"]

        # R05 : Niveau académique
        prereq_score = self._score_prereq_quality(student, program)
        rule_score += prereq_score * self.weights["prereq_match"]

        # R08 : Compétences enseignées pertinentes
        skill_score = self._score_skill_relevance(student, program)
        rule_score += skill_score * self.weights["skill_relevance"]

        # R02b : Fit budget (normalisé)
        budget_score = self._score_budget_fit(student, program)
        rule_score += budget_score * self.weights["budget_fit"]

        # R03b : Fit durée
        duration_score = self._score_duration_fit(student, program)
        rule_score += duration_score * self.weights["duration_fit"]

        # R06 : Localisation
        location_score = self._score_location(student, program)
        rule_score += location_score * self.weights["location_match"]

        # R09 : Satisfaction
        satisfaction_score = self._score_satisfaction(program)
        rule_score += satisfaction_score * self.weights["satisfaction"]

        # R07 : Remote
        if student.constraints.remote_only and program.is_remote:
            rule_score += 0.05
            reasons.append("Formation à distance conforme à la demande")

        # R10 : Langue
        if program.language == "anglais" and not student.constraints.requires_english:
            rule_score -= 0.05
            reasons.append("Formation en anglais (langue non demandée)")

        preference_score = rule_score

        domain_alignment = self._score_domain_alignment(student, program)

        final_score = min(100.0, rule_score * domain_alignment * 100)

        if domain_alignment < 0.3:
            reasons.append(f"Aucun lien avec vos compétences (domaine: {program.domain.value})")
        if interest_score > 0.5:
            reasons.append(f"Bonnes correspondances avec vos intérêts ({program.domain.value})")
        if skill_score > 0.5:
            reasons.append("Bonnes compétences enseignées pour votre profil")
        if budget_score < 0.3 and student.constraints.max_budget is not None:
            reasons.append("Formation coûteuse pour votre budget")

        return ScoredProgram(
            program=program,
            score=round(final_score, 2),
            eligible=eligible,
            rule_score=round(rule_score, 4),
            preference_score=round(preference_score, 4),
            violations=violations,
            reasons=reasons,
        )

    def _check_prerequisites(self, student: Student, program: Program) -> tuple[bool, str]:
        missing = []
        for prereq in program.prerequisites:
            if not prereq.required:
                continue
            student_level = student.get_skill_level(prereq.domain).value
            if LEVEL_ORDER.index(student_level) < LEVEL_ORDER.index(prereq.min_level):
                missing.append(f"{prereq.domain} (requis: {prereq.min_level}, actuel: {student_level})")
        if missing:
            return False, f"Prérequis manquants: {', '.join(missing)}"
        return True, "Tous les prérequis sont satisfaits"

    def _score_prereq_quality(self, student: Student, program: Program) -> float:
        if not program.prerequisites:
            return 1.0
        total = 0.0
        for prereq in program.prerequisites:
            student_idx = LEVEL_ORDER.index(student.get_skill_level(prereq.domain).value)
            req_idx = LEVEL_ORDER.index(prereq.min_level)
            if student_idx >= req_idx:
                bonus = min(1.0, 0.8 + 0.2 * (student_idx - req_idx) / max(1, len(LEVEL_ORDER) - req_idx))
            else:
                bonus = max(0.0, student_idx / max(1, req_idx))
            total += bonus * prereq.weight
        total_weight = sum(p.weight for p in program.prerequisites)
        return total / total_weight if total_weight > 0 else 1.0

    def _score_interest_match(self, student: Student, program: Program) -> float:
        if not student.interests:
            return 0.0
        program_text = f"{program.domain.value} {program.name} {' '.join(program.skills_taught)} {program.description}".lower()
        matches = sum(1 for interest in student.interests if interest.lower() in program_text)
        return min(1.0, matches / max(1, len(student.interests)))

    def _score_skill_relevance(self, student: Student, program: Program) -> float:
        if not program.skills_taught or not student.interests:
            return 0.0
        student_text = " ".join(student.interests).lower()
        matches = sum(1 for skill in program.skills_taught if skill.lower() in student_text)
        return min(1.0, matches / max(1, len(program.skills_taught)))

    def _score_budget_fit(self, student: Student, program: Program) -> float:
        if student.constraints.max_budget is None or student.constraints.max_budget == 0:
            return 0.5
        ratio = program.cost / student.constraints.max_budget
        if ratio <= 0.5:
            return 1.0
        elif ratio <= 1.0:
            return 1.0 - (ratio - 0.5)
        return 0.0

    def _score_duration_fit(self, student: Student, program: Program) -> float:
        if student.constraints.max_duration_months is None:
            return 0.5
        ratio = program.duration_months / student.constraints.max_duration_months
        if ratio <= 0.7:
            return 1.0
        elif ratio <= 1.0:
            return 1.0 - (ratio - 0.7) / 0.3
        return 0.0

    def _score_location(self, student: Student, program: Program) -> float:
        if not student.constraints.preferred_location:
            return 0.5
        if program.location.lower() == student.constraints.preferred_location.lower():
            return 1.0
        return 0.0

    def _score_satisfaction(self, program: Program) -> float:
        if program.satisfaction_rate is None:
            return 0.5
        return program.satisfaction_rate / 100.0

    def _score_domain_alignment(self, student: Student, program: Program) -> float:
        student_domains = {sk.domain.lower() for sk in student.skills}
        student_interests_lower = {i.lower() for i in student.interests}
        program_domain = program.domain.value.lower()
        program_domain_flat = program_domain.replace("_", " ")
        skills_taught_lower = {s.lower() for s in program.skills_taught}

        has_domain_match = program_domain in student_domains or program_domain_flat in student_domains
        has_interest_match = any(
            interest in program_domain_flat or program_domain_flat in interest
            or interest.replace(" ", "_") in program_domain
            or program_domain in interest.replace(" ", "_")
            for interest in student_interests_lower
        )
        has_skill_overlap = bool(student_domains & skills_taught_lower)

        if has_domain_match or has_interest_match:
            return 1.0
        if has_skill_overlap:
            return 0.7
        student_all = student_domains | student_interests_lower
        for sa in student_all:
            sa_flat = sa.replace("_", " ")
            if sa_flat in program_domain_flat or program_domain_flat in sa_flat:
                return 0.85
            for word in program_domain_flat.split():
                if len(word) > 3 and word in sa_flat:
                    return 0.6
        return 0.15
