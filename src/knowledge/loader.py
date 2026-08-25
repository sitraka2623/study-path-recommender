from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.student import Student, Skill, SkillLevel, Constraint
from src.models.program import Program, Prerequisite

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_json(filepath: Path) -> Any:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_programs(filepath: Path | None = None) -> list[Program]:
    path = filepath or DATA_DIR / "programs_catalog.json"
    raw = load_json(path)
    return [Program(**p) for p in raw]


def load_students(filepath: Path | None = None) -> list[Student]:
    path = filepath or DATA_DIR / "sample_students.json"
    raw = load_json(path)
    return [Student(**s) for s in raw]


def load_rules(filepath: Path | None = None) -> dict:
    path = filepath or CONFIG_DIR / "rules.json"
    return load_json(path)


def load_student_by_id(student_id: str, filepath: Path | None = None) -> Student | None:
    students = load_students(filepath)
    for s in students:
        if s.id == student_id:
            return s
    return None


def load_program_by_id(program_id: str, filepath: Path | None = None) -> Program | None:
    programs = load_programs(filepath)
    for p in programs:
        if p.id == program_id:
            return p
    return None
