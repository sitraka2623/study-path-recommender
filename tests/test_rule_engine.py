import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.models.student import Student, Skill, SkillLevel, Constraint
from src.models.program import Program, Prerequisite, Domain, ProgramType
from src.engines.rule_engine import RuleEngine, ScoredProgram
from src.knowledge.loader import load_programs, load_students


@pytest.fixture
def engine():
    return RuleEngine()


@pytest.fixture
def programs():
    return load_programs()


@pytest.fixture
def students():
    return load_students()


def make_student(**kwargs) -> Student:
    defaults = {
        "id": "T00",
        "name": "Test",
        "current_level": "bac+3",
        "skills": [],
        "interests": [],
        "constraints": Constraint(),
    }
    defaults.update(kwargs)
    return Student(**defaults)


class TestPrerequisites:
    def test_eligible_when_prereqs_met(self, engine, programs):
        student = make_student(
            skills=[
                Skill(domain="informatique", level=SkillLevel.ADVANCED),
                Skill(domain="mathematiques", level=SkillLevel.INTERMEDIATE),
            ]
        )
        p = next(p for p in programs if p.id == "P01")
        result = engine._evaluate_single(student, p)
        assert result.eligible

    def test_ineligible_when_prereqs_missing(self, engine, programs):
        student = make_student(
            skills=[Skill(domain="informatique", level=SkillLevel.BEGINNER)]
        )
        p = next(p for p in programs if p.id == "P07")
        result = engine._evaluate_single(student, p)
        assert not result.eligible
        assert any(v.rule_id == "R01" for v in result.violations)

    def test_no_prereqs_always_eligible(self, engine, programs):
        student = make_student()
        p = next(p for p in programs if p.id == "P06")
        result = engine._evaluate_single(student, p)
        assert result.eligible


class TestBudgetConstraint:
    def test_reject_when_over_budget(self, engine):
        student = make_student(constraints=Constraint(max_budget=1000))
        program = Program(
            id="TB1", name="Test", institution="Test", domain=Domain.COMPUTER_SCIENCE,
            program_type=ProgramType.MASTER, duration_months=12,
            cost=5000, location="Paris",
        )
        result = engine._evaluate_single(student, program)
        assert not result.eligible
        assert any(v.rule_id == "R02" for v in result.violations)

    def test_accept_when_under_budget(self, engine):
        student = make_student(constraints=Constraint(max_budget=10000))
        program = Program(
            id="TB2", name="Test", institution="Test", domain=Domain.COMPUTER_SCIENCE,
            program_type=ProgramType.MASTER, duration_months=12,
            cost=5000, location="Paris",
        )
        result = engine._evaluate_single(student, program)
        assert result.eligible

    def test_no_budget_constraint(self, engine):
        student = make_student(constraints=Constraint(max_budget=None))
        program = Program(
            id="TB3", name="Test", institution="Test", domain=Domain.COMPUTER_SCIENCE,
            program_type=ProgramType.MASTER, duration_months=12,
            cost=99999, location="Paris",
        )
        result = engine._evaluate_single(student, program)
        assert result.eligible


class TestDurationConstraint:
    def test_reject_when_over_duration(self, engine):
        student = make_student(constraints=Constraint(max_duration_months=6))
        program = Program(
            id="TD1", name="Test", institution="Test", domain=Domain.COMPUTER_SCIENCE,
            program_type=ProgramType.MASTER, duration_months=24,
            cost=500, location="Paris",
        )
        result = engine._evaluate_single(student, program)
        assert not result.eligible


class TestInterestMatching:
    def test_high_score_when_interests_match(self, engine):
        student = make_student(interests=["intelligence artificielle", "machine learning"])
        program = Program(
            id="TI1", name="Master IA", institution="Test",
            domain=Domain.AI, program_type=ProgramType.MASTER,
            duration_months=24, cost=500, location="Paris",
            skills_taught=["Machine Learning", "Deep Learning"],
        )
        result = engine._evaluate_single(student, program)
        assert result.score > 30

    def test_low_score_when_no_match(self, engine):
        student = make_student(interests=["droit", "philosophie"])
        program = Program(
            id="TI2", name="Master IA", institution="Test",
            domain=Domain.AI, program_type=ProgramType.MASTER,
            duration_months=24, cost=500, location="Paris",
            skills_taught=["Machine Learning", "Deep Learning"],
        )
        result = engine._evaluate_single(student, program)
        assert result.score < 50


class TestFullEvaluation:
    def test_returns_sorted_results(self, engine, programs):
        student = make_student(
            current_level="bac+3",
            skills=[
                Skill(domain="informatique", level=SkillLevel.INTERMEDIATE, grade=14),
                Skill(domain="mathematiques", level=SkillLevel.INTERMEDIATE, grade=13),
            ],
            interests=["informatique", "data science"],
            constraints=Constraint(max_budget=5000),
        )
        results = engine.evaluate(student, programs)
        assert len(results) == len(programs)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_eligible_programs_prioritized(self, engine, programs):
        student = make_student(
            skills=[Skill(domain="informatique", level=SkillLevel.BEGINNER)],
            interests=["informatique"],
            constraints=Constraint(max_budget=10000, max_duration_months=12),
        )
        results = engine.evaluate(student, programs)
        eligible = [r for r in results if r.eligible]
        ineligible = [r for r in results if not r.eligible]
        if eligible and ineligible:
            assert eligible[0].score >= ineligible[-1].score
