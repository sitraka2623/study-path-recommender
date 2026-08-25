from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Domain(str, Enum):
    COMPUTER_SCIENCE = "informatique"
    DATA_SCIENCE = "data_science"
    AI = "intelligence_artificielle"
    BUSINESS = "gestion"
    MARKETING = "marketing"
    LAW = "droit"
    MEDICINE = "medecine"
    ENGINEERING = "ingenierie"
    DESIGN = "design"
    LANGUAGES = "langues"
    PSYCHOLOGY = "psychologie"
    BIOLOGY = "biologie"
    PHYSICS = "physique"
    MATHEMATICS = "mathematiques"
    OTHER = "autre"


class ProgramType(str, Enum):
    LICENSE = "licence"
    MASTER = "master"
    MBA = "mba"
    ENGINEERING_DEGREE = "diplome_ingenieur"
    BOOTCAMP = "bootcamp"
    CERTIFICATE = "certificat"
    PROFESSIONAL_DEGREE = "diplome_pro"
    DOCTORATE = "doctorat"


class Prerequisite(BaseModel):
    domain: str
    min_level: str = Field("beginner", description="Niveau minimum requis")
    required: bool = True
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Poids dans le scoring")


class Program(BaseModel):
    id: str
    name: str
    institution: str
    domain: Domain
    program_type: ProgramType
    duration_months: int
    cost: float = Field(ge=0, description="Coût total en euros")
    location: str
    is_remote: bool = False
    prerequisites: list[Prerequisite] = Field(default_factory=list)
    skills_taught: list[str] = Field(default_factory=list)
    career_outcomes: list[str] = Field(default_factory=list)
    satisfaction_rate: Optional[float] = Field(None, ge=0, le=100)
    description: str = ""
    language: str = "français"
    max_students: Optional[int] = None
    deadline: Optional[str] = None

    def is_eligible(self, student_skills: dict[str, str]) -> bool:
        for prereq in self.prerequisites:
            if not prereq.required:
                continue
            level_order = ["none", "beginner", "intermediate", "advanced", "expert"]
            student_level = student_skills.get(prereq.domain.lower(), "none")
            if level_order.index(student_level) < level_order.index(prereq.min_level):
                return False
        return True

    def to_context_string(self) -> str:
        lines = [
            f"Formation: {self.name} ({self.institution})",
            f"Type: {self.program_type.value}, Domaine: {self.domain.value}",
            f"Durée: {self.duration_months} mois, Coût: {self.cost}€",
            f"Localisation: {self.location}" + (" (à distance)" if self.is_remote else ""),
            f"Langue: {self.language}",
        ]
        if self.prerequisites:
            prereqs = ", ".join(
                f"{p.domain}({p.min_level})" for p in self.prerequisites if p.required
            )
            lines.append(f"Prérequis: {prereqs}")
        if self.skills_taught:
            lines.append(f"Compétences enseignées: {', '.join(self.skills_taught)}")
        if self.career_outcomes:
            lines.append(f"Débouchés: {', '.join(self.career_outcomes)}")
        if self.description:
            lines.append(f"Description: {self.description}")
        return "\n".join(lines)
