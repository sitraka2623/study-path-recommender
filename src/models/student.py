from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    domain: str
    level: SkillLevel
    grade: Optional[float] = Field(None, ge=0, le=20, description="Note sur 20 si disponible")


class Constraint(BaseModel):
    max_budget: Optional[float] = Field(None, ge=0, description="Budget max en euros")
    max_duration_months: Optional[int] = Field(None, ge=1, description="Durée max en mois")
    preferred_location: Optional[str] = None
    requires_english: bool = False
    remote_only: bool = False


class Student(BaseModel):
    id: str
    name: str
    current_level: str = Field(..., description="Dernier diplôme obtenu (ex: Bac, L2, Master 1)")
    skills: list[Skill] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list, description="Domaines d'intérêt en texte libre")
    constraints: Constraint = Field(default_factory=Constraint)
    free_text: Optional[str] = Field(None, description="Description libre du profil, motivation, projet")

    def get_skill_level(self, domain: str) -> SkillLevel:
        for skill in self.skills:
            if skill.domain.lower() == domain.lower():
                return skill.level
        return SkillLevel.NONE

    def has_skill(self, domain: str, min_level: SkillLevel = SkillLevel.BEGINNER) -> bool:
        level_order = list(SkillLevel)
        current = self.get_skill_level(domain)
        return level_order.index(current) >= level_order.index(min_level)

    def get_average_grade(self) -> Optional[float]:
        grades = [s.grade for s in self.skills if s.grade is not None]
        return sum(grades) / len(grades) if grades else None

    def to_context_string(self) -> str:
        lines = [f"Étudiant: {self.name}, Niveau actuel: {self.current_level}"]
        if self.skills:
            skills_str = ", ".join(f"{s.domain} ({s.level.value})" for s in self.skills)
            lines.append(f"Compétences: {skills_str}")
        if self.interests:
            lines.append(f"Intérêts: {', '.join(self.interests)}")
        if self.constraints.max_budget is not None:
            lines.append(f"Budget max: {self.constraints.max_budget}€")
        if self.constraints.max_duration_months is not None:
            lines.append(f"Durée max: {self.constraints.max_duration_months} mois")
        if self.constraints.preferred_location:
            lines.append(f"Localisation préférée: {self.constraints.preferred_location}")
        if self.free_text:
            lines.append(f"À propos: {self.free_text}")
        return "\n".join(lines)


class StudentProfile(BaseModel):
    """Profil complet avec scoring d'incertitude."""
    student: Student
    completeness_score: float = Field(0.0, ge=0.0, le=1.0)
    contradictions: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
