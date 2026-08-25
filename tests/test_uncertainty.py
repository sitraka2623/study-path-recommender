import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.utils.uncertainty import UncertaintyAnalyzer, UncertaintyReport
from src.models.student import Student, Skill, SkillLevel, Constraint


def make_student(**kwargs) -> Student:
    defaults = {
        "id": "TU0",
        "name": "Test Uncertainty",
        "current_level": "bac+3",
        "skills": [
            Skill(domain="informatique", level=SkillLevel.INTERMEDIATE, grade=14),
        ],
        "interests": ["informatique"],
        "constraints": Constraint(max_budget=5000, max_duration_months=24),
        "free_text": "Je veux progresser en informatique.",
    }
    defaults.update(kwargs)
    return Student(**defaults)


@pytest.fixture
def analyzer():
    return UncertaintyAnalyzer()


class TestCompleteness:
    def test_full_profile_high_completeness(self, analyzer):
        student = make_student()
        report = analyzer.analyze(student)
        assert report.completeness >= 0.6

    def test_empty_profile_low_completeness(self, analyzer):
        student = make_student(
            current_level="",
            skills=[],
            interests=[],
            constraints=Constraint(),
            free_text=None,
        )
        report = analyzer.analyze(student)
        assert report.completeness <= 0.1

    def test_partial_profile_medium_completeness(self, analyzer):
        student = make_student(
            skills=[],
            interests=["informatique"],
            constraints=Constraint(max_budget=5000),
        )
        report = analyzer.analyze(student)
        assert 0.2 <= report.completeness <= 0.6


class TestMissingInfo:
    def test_detects_missing_budget(self, analyzer):
        student = make_student(constraints=Constraint())
        report = analyzer.analyze(student)
        assert any("Budget" in m for m in report.missing_info)

    def test_detects_missing_location(self, analyzer):
        student = make_student(constraints=Constraint(max_budget=5000))
        report = analyzer.analyze(student)
        assert any("Localisation" in m or "localisation" in m for m in report.missing_info)

    def test_no_missing_for_full_profile(self, analyzer):
        student = make_student(
            constraints=Constraint(
                max_budget=5000, max_duration_months=24, preferred_location="Paris"
            ),
            skills=[
                Skill(domain="informatique", level=SkillLevel.ADVANCED),
                Skill(domain="mathematiques", level=SkillLevel.INTERMEDIATE),
                Skill(domain="physique", level=SkillLevel.BEGINNER),
            ],
            interests=["informatique", "IA"],
        )
        report = analyzer.analyze(student)
        assert len(report.missing_info) <= 1


class TestContradictions:
    def test_detects_high_skill_low_grade(self, analyzer):
        student = make_student(
            skills=[
                Skill(domain="informatique", level=SkillLevel.EXPERT, grade=6),
            ],
        )
        report = analyzer.analyze(student)
        assert len(report.contradictions) > 0

    def test_no_contradiction_normal_profile(self, analyzer):
        student = make_student(
            skills=[
                Skill(domain="informatique", level=SkillLevel.INTERMEDIATE, grade=14),
            ],
        )
        report = analyzer.analyze(student)
        assert len(report.contradictions) == 0


class TestWarnings:
    def test_zero_budget_warning(self, analyzer):
        student = make_student(constraints=Constraint(max_budget=0))
        report = analyzer.analyze(student)
        assert any("0€" in w for w in report.warnings)

    def test_low_grades_warning(self, analyzer):
        student = make_student(
            skills=[
                Skill(domain="informatique", level=SkillLevel.BEGINNER, grade=8),
                Skill(domain="mathematiques", level=SkillLevel.BEGINNER, grade=7),
            ],
        )
        report = analyzer.analyze(student)
        assert any("10/20" in w for w in report.warnings)


class TestConfidenceModifier:
    def test_modifier_negative_for_incomplete(self, analyzer):
        student = make_student(
            current_level="",
            skills=[],
            interests=[],
            constraints=Constraint(),
            free_text=None,
        )
        report = analyzer.analyze(student)
        assert report.confidence_modifier < 0

    def test_modifier_positive_for_complete(self, analyzer):
        student = make_student(
            skills=[
                Skill(domain="informatique", level=SkillLevel.ADVANCED, grade=16),
                Skill(domain="mathematiques", level=SkillLevel.INTERMEDIATE, grade=14),
                Skill(domain="physique", level=SkillLevel.BEGINNER, grade=12),
            ],
            interests=["informatique", "IA", "data science"],
            constraints=Constraint(max_budget=5000, max_duration_months=24, preferred_location="Paris"),
            free_text="Je veux devenir data scientist.",
        )
        report = analyzer.analyze(student)
        assert report.confidence_modifier >= 0
